import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import urllib
import os
from dotenv import load_dotenv
import time
from openai import AzureOpenAI
import requests
import jwt

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="EduInnovatech Exam Monitor",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Cargar variables de entorno
load_dotenv()

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    .student-card {
        background-color: #ffffff;
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 10px;
        margin-bottom: 10px;
    }
    .card-header { font-weight: bold; font-size: 1.1em; }
    .card-metric { font-size: 0.9em; color: gray; }
    .answer-row { font-size: 0.85em; margin-bottom: 2px; }
    .correct { color: green; }
    .incorrect { color: red; }
    </style>
    """, unsafe_allow_html=True)

# --- CAPA DE SERVICIOS ---

@st.cache_resource
def get_db_engine():
    try:
        conn_str = os.getenv("AZURE_SQL_CONNECTION_STRING")
        if not conn_str:
            server = os.getenv('DB_SERVER')
            database = os.getenv('DB_NAME')
            username = os.getenv('DB_USER')
            password = os.getenv('DB_PASSWORD')
            driver = '{ODBC Driver 18 for SQL Server}'
            params = urllib.parse.quote_plus(
                f'DRIVER={driver};SERVER={server};PORT=1433;DATABASE={database};UID={username};PWD={password};Encrypt=yes;TrustServerCertificate=yes'
            )
            return create_engine(f'mssql+pyodbc:///?odbc_connect={params}', pool_pre_ping=True, pool_recycle=3600)
        return create_engine(f'mssql+pyodbc:///?odbc_connect={urllib.parse.quote_plus(conn_str)}', pool_pre_ping=True, pool_recycle=3600)
    except Exception:
        return None

def send_signalr_broadcast(message_text):
    conn_str = os.getenv("AZURE_SIGNALR_CONNECTION_STRING")
    if not conn_str: return False
    try:
        endpoint = conn_str.split(";")[0].replace("Endpoint=", "")
        access_key = conn_str.split(";")[1].replace("AccessKey=", "")
        api_url = f"{endpoint}/api/v1/hubs/olimpiada_hub"
        
        payload = {"iat": int(time.time()), "exp": int(time.time()) + 3600, "aud": api_url}
        token = jwt.encode(payload, access_key, algorithm="HS256")
        
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        data = {"target": "*", "arguments": [message_text]}
        return requests.post(api_url, json=data, headers=headers).status_code == 200
    except:
        return False

# --- VISTA: PROFESOR (MONITOR DE EXAMEN) ---
def vista_profesor(engine):
    st.title("👨‍🏫 Monitor de Examen: Matemáticas")
    st.caption("Visualizando respuestas en tiempo real de la clase de 1ºA")

    if not engine: st.error("Sin conexión a BD"); return

    with engine.connect() as conn:
        # Traer todo el historial del examen actual
        df = pd.read_sql("SELECT * FROM Students WHERE Subject = 'Matemáticas' ORDER BY ExamDate DESC", conn)

    if not df.empty:
        # Calcular métricas acumuladas por alumno
        student_stats = df.groupby('Name').agg(
            AvgScore=('Score', 'mean'),
            QuestionsDone=('Id', 'count'),
            CorrectAnswers=('IsCorrect', 'sum')
        ).reset_index()
        
        # TABLERO KANBAN DE ALUMNOS
        st.markdown(f"### 📋 Alumnos Activos ({len(student_stats)})")
        
        cols = st.columns(4)
        for idx, row in student_stats.iterrows():
            col = cols[idx % 4]
            with col:
                # Determinar color de tarjeta
                score = row['AvgScore']
                status_color = "green" if score >= 70 else "orange" if score >= 50 else "red"
                
                with st.expander(f"👤 {row['Name']} ({score:.0f}/100)", expanded=True):
                    st.progress(row['AvgScore']/100, text=f"Progreso: {row['QuestionsDone']} preguntas")
                    
                    # Mostrar últimas 3 respuestas CON EL CONTENIDO REAL
                    student_history = df[df['Name'] == row['Name']].head(3)
                    st.markdown("---")
                    for _, ex in student_history.iterrows():
                        icon = "✅" if ex['IsCorrect'] else "❌"
                        # Aquí mostramos: Icono | Pregunta | RESPUESTA DEL ALUMNO
                        st.markdown(f"{icon} **{ex['ExerciseName']}**")
                        st.markdown(f"&nbsp;&nbsp;&nbsp;↳ ✍️ *{ex['StudentAnswer']}*")

        # ZONA DE DATOS GLOBALES
        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### 📊 Rendimiento del Examen")
            st.bar_chart(student_stats.set_index('Name')['AvgScore'])
        with c2:
            st.markdown("### 🛑 Alumnos en Dificultad")
            # Mostrar tabla detallada de los que van mal
            low_performers = student_stats[student_stats['AvgScore'] < 50]
            st.dataframe(low_performers[['Name', 'AvgScore', 'QuestionsDone']], hide_index=True)

    else:
        st.info("ℹ️ Esperando a que comience el examen (inicia 'data_generator.py')...")

# --- VISTA: FAMILIA ---
def vista_familia(engine):
    st.title("👨‍👩‍👧‍👦 Portal de Familias")
    st.markdown("Seguimiento detallado del examen de Matemáticas.")

    if not engine: st.error("Error BD"); return

    with engine.connect() as conn:
        students_list = pd.read_sql("SELECT DISTINCT Name FROM Students WHERE Subject='Matemáticas' ORDER BY Name", conn)['Name'].tolist()

    selected_student = st.selectbox("Seleccionar Alumno", ["-- Seleccionar --"] + students_list)

    if selected_student != "-- Seleccionar --":
        with engine.connect() as conn:
            df_student = pd.read_sql(f"SELECT * FROM Students WHERE Name = '{selected_student}' AND Subject='Matemáticas' ORDER BY ExamDate DESC", conn)
        
        if not df_student.empty:
            st.divider()
            st.header(f"Examen de {selected_student}")
            
            # KPIs
            score = df_student['Score'].mean()
            correct = df_student['IsCorrect'].sum()
            total = len(df_student)
            
            k1, k2, k3 = st.columns(3)
            k1.metric("Nota Actual", f"{score:.1f}/100")
            k2.metric("Preguntas", total)
            k3.metric("Aciertos", f"{correct}")
            
            # Tabla detallada con respuestas
            st.subheader("📝 Respuestas Enviadas")
            
            display_df = df_student[['ExamDate', 'ExerciseName', 'StudentAnswer', 'IsCorrect', 'Score']].copy()
            # Formateo visual
            display_df['IsCorrect'] = display_df['IsCorrect'].apply(lambda x: "✅" if x else "❌")
            
            st.dataframe(
                display_df, 
                column_config={
                    "ExerciseName": "Pregunta",
                    "StudentAnswer": "Respuesta Alumno",
                    "IsCorrect": "Resultado"
                },
                hide_index=True,
                use_container_width=True
            )
        else:
            st.warning("Sin datos para este examen.")

# --- ROUTER ---
def main():
    engine = get_db_engine()
    
    with st.sidebar:
        st.image("https://img.icons8.com/3d-fluency/94/test-passed.png", width=60)
        st.title("EduInnovatech")
        role = st.radio("Entrar como:", ["Profesor", "Familia"])
        st.divider()
        st.info("Examen Activo: Matemáticas")

    if role == "Profesor":
        vista_profesor(engine)
    else:
        vista_familia(engine)

if __name__ == "__main__":
    main()