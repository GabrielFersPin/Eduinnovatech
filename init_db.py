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
driver = '{ODBC Driver 18 for SQL Server}' # Actualizado a 18

def init_database():
    print("--- 🛠️ INICIALIZANDO BASE DE DATOS EDUINNOVATECH ---")
    
    conn_str = f'DRIVER={driver};SERVER={server};PORT=1433;DATABASE={database};UID={username};PWD={password};Encrypt=yes;TrustServerCertificate=yes'
    
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        # SQL para crear la tabla Students
        create_table_sql = """
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Students' AND xtype='U')
        BEGIN
            CREATE TABLE Students (
                Id INT IDENTITY(1,1) PRIMARY KEY,
                Name NVARCHAR(100),
                Subject NVARCHAR(50),
                Score INT,
                ExamDate DATETIME
            )
            PRINT '✅ Tabla Students creada correctamente.'
        END
        ELSE
        BEGIN
            PRINT 'ℹ️ La tabla Students ya existe.'
        END
        """
        
        cursor.execute(create_table_sql)
        conn.commit()
        print("--- FINALIZADO ---")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    init_database()
