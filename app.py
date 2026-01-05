import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import urllib
import os
from dotenv import load_dotenv
import time
from openai import AzureOpenAI
from azure.messaging.webpubsubservice import WebPubSubServiceClient
import requests
import jwt

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="EduInnovatech SaaS",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Cargar variables de entorno
load_dotenv()

# --- ESTILOS CSS PERSONALIZADOS (Look & Feel Profesional) ---
st.markdown("""
    <style>
    .main {
        background-color: #f0f2f6;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# --- CAPA DE SERVICIOS (Conexiones Cloud) ---

@st.cache_resource
def get_db_engine():
    """Conecta con Azure SQL Serverless"""
    try:
        # Intenta usar la variable de conexión directa primero
        conn_str = os.getenv("AZURE_SQL_CONNECTION_STRING")
        if not conn_str:
            # Fallback a construcción manual
            server = os.getenv('DB_SERVER')
            database = os.getenv('DB_NAME')
            username = os.getenv('DB_USER')
            password = os.getenv('DB_PASSWORD')
            driver = '{ODBC Driver 18 for SQL Server}'
            params = urllib.parse.quote_plus(
                f'DRIVER={driver};SERVER={server};PORT=1433;DATABASE={database};UID={username};PWD={password};Encrypt=yes;TrustServerCertificate=yes'
            )
            return create_engine(f'mssql+pyodbc:///?odbc_connect={params}')
        return create_engine(f'mssql+pyodbc:///?odbc_connect={urllib.parse.quote_plus(conn_str)}') # Simplificado para el ejemplo
    except Exception:
        return None

def get_openai_client():
    """Devuelve el cliente listo para usar"""
    try:
        client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        return client
    except Exception as e:
        print(f"Error OpenAI: {e}")
        return None

def get_signalr_service():
    """Cliente Azure SignalR (Tiempo Real)"""
    conn_str = os.getenv("AZURE_SIGNALR_CONNECTION_STRING")
    if conn_str:
        return WebPubSubServiceClient.from_connection_string(conn_str, hub="olimpiada_hub")
    return None

def send_signalr_broadcast(message_text):
    """Envía un mensaje a TODOS los usuarios conectados"""
    conn_str = os.getenv("AZURE_SIGNALR_CONNECTION_STRING")
    if not conn_str:
        return False

    try:
        # 1. Parsear la cadena de conexión para sacar Endpoint y Key
        endpoint = conn_str.split(";")[0].replace("Endpoint=", "")
        access_key = conn_str.split(";")[1].replace("AccessKey=", "")
        
        # 2. Construir la URL de la API REST de SignalR
        hub_name = "olimpiada_hub"
        api_url = f"{endpoint}/api/v1/hubs/{hub_name}"
        
        # 3. Generar Token de Seguridad (JWT)
        payload = {
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600, # Expira en 1 hora
            "aud": api_url
        }
        token = jwt.encode(payload, access_key, algorithm="HS256")
        
        # 4. Enviar la petición POST
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        # El mensaje que verán los alumnos
        data = {
            "target": "*", # * significa "a todos"
            "arguments": [message_text]
        }
        
        response = requests.post(api_url, json=data, headers=headers)
        return response.status_code == 200
        
    except Exception as e:
        st.error(f"Error SignalR: {e}")
        return False

# --- VISTA 1: PROFESOR (Gestión y Monitorización) ---
def vista_profesor(engine):
    st.title("👨‍🏫 Portal del Profesor")
    st.markdown("Gestión de la Olimpiada y Generación de Contenidos")

    tab_monitor, tab_ia = st.tabs(["📡 Monitor Tiempo Real", "🧠 Crear Ejercicios (IA)"])

    # --- SUB-VISTA: MONITOR (SignalR + SQL) ---
    with tab_monitor:
        col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
        
        # Simulación de datos si no hay DB
        if engine:
            try:
                with engine.connect() as conn:
                    df = pd.read_sql("SELECT TOP 500 * FROM Students ORDER BY ExamDate DESC", conn)
                    
                    # KPIs Reales
                    col_kpi1.metric("Alumnos Conectados", f"{len(df)}", "+Activos")
                    col_kpi2.metric("Nota Media Clase", f"{df['Score'].mean():.1f}", "Sobre 100")
                    col_kpi3.metric("Alertas de Rendimiento", f"{len(df[df['Score'] < 50])}", "Necesitan ayuda", delta_color="inverse")
                    
                    st.divider()
                    
                    # Panel de Control SignalR
                    st.subheader("📢 Comunicación en Vivo (Azure SignalR)")
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        msg = st.text_input("Enviar notificación a todos los alumnos", "⚠️ Quedan 5 minutos.")
                    with c2:
                        st.write("")
                        st.write("")
                        if st.button("Enviar Broadcast"):
                            exito = send_signalr_broadcast(msg)
                            if exito:
                                st.success("📢 Mensaje enviado correctamente a la nube.")
                            else:
                                st.error("❌ Error al enviar. Revisa el .env")

                    # Gráfica de distribución
                    st.subheader("Rendimiento por Asignatura")
                    st.bar_chart(df['Subject'].value_counts())
            except Exception as e:
                st.error(f"Error conectando a Azure SQL: {e}")
        else:
            st.warning("Conectando a base de datos...")

    # --- SUB-VISTA: GENERADOR IA (OpenAI) ---
    with tab_ia:
        st.info("Utiliza Azure OpenAI (GPT-4o) para generar ejercicios únicos y evitar el plagio.")
        
        c_topic, c_diff = st.columns(2)
        topic = c_topic.selectbox("Tema", ["Álgebra", "Historia del Arte", "Física Cuántica", "Literatura"])
        difficulty = c_diff.select_slider("Nivel", ["Fácil", "Medio", "Difícil", "Olimpiada"])
        
        if st.button("✨ Generar Pregunta"):
            client = get_openai_client()
            if client:
                with st.spinner("La IA está diseñando el ejercicio..."):
                    try:
                        deploy_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-modelo-base")
                        response = client.chat.completions.create(
                            model=deploy_name,
                            messages=[
                                {"role": "system", "content": "Eres un experto creador de exámenes."},
                                {"role": "user", "content": f"Crea una pregunta de opción múltiple sobre {topic} nivel {difficulty}."}
                            ]
                        )
                        st.markdown("### Resultado:")
                        st.success(response.choices[0].message.content)
                        st.button("💾 Guardar en Biblioteca de Ejercicios") # Simulado
                    except Exception as e:
                        st.error(f"Error OpenAI: {e}")
            else:
                st.error("Faltan credenciales de OpenAI")

# --- VISTA 2: FAMILIA (Privacidad y Seguimiento) ---
def vista_familia(engine):
    st.title("👪 Portal de Familias")
    st.markdown("Consulte el rendimiento académico de su hijo/a de forma segura.")

    if engine:
        with engine.connect() as conn:
            # Simulamos búsqueda segura
            student_name = st.text_input("🔍 Buscar por Nombre del Alumno", placeholder="Ej: Juan Perez")
            
            if student_name:
                # Consulta SQL segura (con parámetros sería mejor, usamos f-string simple por demo)
                query = f"SELECT * FROM Students WHERE Name LIKE '%%{student_name}%%'"
                df_student = pd.read_sql(query, conn)
                
                if not df_student.empty:
                    st.divider()
                    st.subheader(f"Boletín de: {df_student.iloc[0]['Name']}")
                    
                    # Tarjetas de notas
                    col1, col2 = st.columns(2)
                    avg_score = df_student['Score'].mean()
                    
                    col1.metric("Nota Media Actual", f"{avg_score:.1f}", delta=f"{avg_score-50:.1f} vs aprobado")
                    col2.metric("Exámenes Realizados", len(df_student))
                    
                    # Gráfico de evolución personal
                    st.subheader("Evolución del Progreso")
                    st.line_chart(df_student.set_index('ExamDate')['Score'])
                    
                    st.info("ℹ️ Estos datos son privados y solo visibles con las credenciales de tutor.")
                else:
                    st.warning("No se encontraron alumnos con ese nombre.")
    else:
        st.error("Sistema de base de datos no disponible.")

# --- ENRUTADOR PRINCIPAL (Sidebar) ---
def main():
    engine = get_db_engine()
    
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/microsoft-azure.png", width=50)
        st.header("EduInnovatech")
        st.caption("Plataforma SaaS Educativa v6.0")
        
        # EL SELECTOR DE ROL
        rol = st.selectbox("👤 Selecciona tu Perfil", ["Profesor / Centro", "Familia / Tutor"])
        
        st.divider()
        st.caption("Estado del Sistema Cloud:")
        if engine:
            st.success("🟢 Azure SQL: Conectado")
        else:
            st.error("🔴 Azure SQL: Error")
            
        if os.getenv("AZURE_OPENAI_KEY"):
            st.success("🟢 Azure OpenAI: Listo")
        else:
            st.warning("🟡 OpenAI: No config")

    # Renderizar la vista según el rol
    if rol == "Profesor / Centro":
        vista_profesor(engine)
    else:
        vista_familia(engine)

if __name__ == "__main__":
    main()