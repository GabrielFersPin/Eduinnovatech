import pyodbc
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración
server = os.getenv('DB_SERVER')
database = os.getenv('DB_NAME')
username = os.getenv('DB_USER')
password = os.getenv('DB_PASSWORD')
driver = '{ODBC Driver 18 for SQL Server}' 

def init_database():
    print("--- 🛠️ INICIALIZANDO BASE DE DATOS EDUINNOVATECH (v3 - Exam Simulation) ---")
    
    conn_str = f'DRIVER={driver};SERVER={server};PORT=1433;DATABASE={database};UID={username};PWD={password};Encrypt=yes;TrustServerCertificate=yes'
    
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        # 1. Eliminar tabla anterior si existe (RESET)
        print("⚠️ Eliminando tabla antigua...")
        cursor.execute("IF OBJECT_ID('Students', 'U') IS NOT NULL DROP TABLE Students")
        conn.commit()

        # 2. Crear nueva tabla con esquema detallado
        print("🏗️ Creando nueva tabla 'Students' para examen específico...")
        create_table_sql = """
        CREATE TABLE Students (
            Id INT IDENTITY(1,1) PRIMARY KEY,
            Name NVARCHAR(100),
            Subject NVARCHAR(50),
            Score INT,
            ExamDate DATETIME,
            ExerciseName NVARCHAR(100),
            IsCorrect BIT,
            StudentAnswer NVARCHAR(255) -- Nuevo: Respuesta del alumno (e.g., 'x = 10')
        )
        """
        cursor.execute(create_table_sql)
        conn.commit()
        print("✅ Tabla Students recreada correctamente.")
        print("--- FINALIZADO ---")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    init_database()
