import pyodbc
import time
import random
import os
from faker import Faker
from datetime import datetime
from dotenv import load_dotenv

# 1. Cargar variables de entorno (Tus secretos)
load_dotenv()

# 2. Configuración de conexión leyendo del .env
server = os.getenv('DB_SERVER')
database = os.getenv('DB_NAME')
username = os.getenv('DB_USER')
password = os.getenv('DB_PASSWORD')
driver = '{ODBC Driver 17 for SQL Server}' # Si falla, prueba con 18

# Inicializar generador de datos falsos (Español)
fake = Faker('es_ES')

# Lista de asignaturas para variar
subjects = ['Matemáticas', 'Historia', 'Física', 'Literatura', 'Inglés', 'Programación Cloud', 'Bases de Datos']

def get_connection():
    # Construir cadena de conexión segura
    conn_str = f'DRIVER={driver};SERVER={server};PORT=1433;DATABASE={database};UID={username};PWD={password}'
    try:
        return pyodbc.connect(conn_str)
    except Exception as e:
        print(f"❌ Error conectando a Azure: {e}")
        return None

def insert_student(cursor):
    # Generar datos aleatorios realistas
    name = fake.name()
    subject = random.choice(subjects)
    score = random.randint(0, 100) # Nota de 0 a 100
    exam_date = datetime.now()

    # Query SQL optimizada
    query = "INSERT INTO Students (Name, Subject, Score, ExamDate) VALUES (?, ?, ?, ?)"
    cursor.execute(query, (name, subject, score, exam_date))
    
    print(f"🚀 Enviado a Azure: {name} | 📚 {subject} | 📝 Nota: {score}")

def start_simulation():
    print("--- 📡 INICIANDO SIMULADOR EDUINNOVATECH ---")
    print(f"Objetivo: {server}")
    print("Presiona CTRL + C para detener.")
    print("----------------------------------------------")

    conn = get_connection()
    if not conn:
        return

    cursor = conn.cursor()

    try:
        while True:
            insert_student(cursor)
            conn.commit() # ¡Importante! Guardar el cambio en la nube
            
            # Esperar entre 1 y 4 segundos para dar sensación de ritmo
            sleep_time = random.randint(1, 4)
            time.sleep(sleep_time)

    except KeyboardInterrupt:
        print("\n🛑 Simulación detenida por el usuario.")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
    finally:
        if conn:
            conn.close()
            print("🔒 Conexión cerrada.")

if __name__ == "__main__":
    start_simulation()