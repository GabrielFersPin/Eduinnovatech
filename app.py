import streamlit as st
import pandas as pd
import pyodbc
from sqlalchemy import create_engine
import urllib
import os
from dotenv import load_dotenv
import time
import altair as alt

# 1. Configuración de página
st.set_page_config(
    page_title="Eduinnovatech Monitor",
    page_icon="🎓",
    layout="wide"
)

# 2. Cargar secretos (Igual que en tus scripts anteriores)
load_dotenv()

# Función para conectar a Azure SQL (con caché para no saturar)
def get_connection():
    server = os.getenv('DB_SERVER')
    database = os.getenv('DB_NAME')
    username = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')
    driver = '{ODBC Driver 18 for SQL Server}'
    
    # Construir cadena de conexión para SQLAlchemy
    params = urllib.parse.quote_plus(
        f'DRIVER={driver};SERVER={server};PORT=1433;DATABASE={database};UID={username};PWD={password};Encrypt=yes;TrustServerCertificate=yes'
    )
    conn_str = f'mssql+pyodbc:///?odbc_connect={params}'
    engine = create_engine(conn_str)
    return engine.connect()

# 3. Función para leer datos
def load_data():
    conn = get_connection()
    # Traemos los últimos 100 registros para ver el tiempo real
    query = "SELECT TOP 100 * FROM Students ORDER BY ExamDate DESC"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# --- INTERFAZ ---

st.title("🎓 Eduinnovatech: Real-Time Exam Monitor")
st.markdown("Monitorización en vivo de la ingesta de exámenes en **Azure SQL Database**.")

# Contenedor para métricas en tiempo real
placeholder = st.empty()

# Bucle de actualización (Simula un dashboard vivo)
# En producción real, usaríamos st.connection o callbacks, pero esto es visualmente efectivo para la demo.
for seconds in range(200):
    try:
        df = load_data()
        
        with placeholder.container():
            # Métricas KPI (Top de la página)
            kpi1, kpi2, kpi3 = st.columns(3)
            
            # KPI 1: Total Exámenes
            kpi1.metric(
                label="Exámenes Procesados",
                value=len(df),
                delta=len(df) - 90 # Simulación de cambio
            )
            
            # KPI 2: Nota Media
            avg_score = df['Score'].mean()
            kpi2.metric(
                label="Nota Media Global",
                value=f"{avg_score:.2f}",
                delta=f"{avg_score - 50:.2f}"
            )
            
            # KPI 3: Último alumno
            last_student = df.iloc[0]['Name'] if not df.empty else "N/A"
            kpi3.metric(label="Último Ingreso", value=last_student)

            # Gráficos (Dos columnas)
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### 📊 Distribución por Asignatura")
                # Gráfico de barras simple
                chart_data = df['Subject'].value_counts().reset_index()
                chart_data.columns = ['Asignatura', 'Exámenes']
                st.bar_chart(chart_data, x='Asignatura', y='Exámenes')

            with col2:
                st.markdown("### 📈 Notas en Tiempo Real")
                # Gráfico de líneas (Evolución de notas)
                st.line_chart(df[['Score']].reset_index(drop=True))

            # Tabla de datos crudos
            with st.expander("Ver Datos Crudos (Azure SQL)"):
                st.dataframe(df)
                
        time.sleep(2) # Refrescar cada 2 segundos

    except Exception as e:
        st.error(f"Error de conexión: {e}")
        st.stop()