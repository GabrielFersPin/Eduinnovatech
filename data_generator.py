import pyodbc
import time
import random
import os
from faker import Faker
from datetime import datetime
from dotenv import load_dotenv
import requests
import jwt

# 1. Cargar variables de entorno
load_dotenv()

# 2. Configuración de conexión
server = os.getenv('DB_SERVER')
database = os.getenv('DB_NAME')
username = os.getenv('DB_USER')
password = os.getenv('DB_PASSWORD')
driver = '{ODBC Driver 18 for SQL Server}' 

fake = Faker('es_ES')

# --- CONFIGURACIÓN DEL EXAMEN ---
CURRENT_SUBJECT = "Matemáticas"
EXAM_TOPIC = "Álgebra Lineal & Cálculo"

# Lista fija de alumnos (Clase 1ºA)
STUDENTS = [
    "Juan Pérez", "María García", "Carlos López", "Ana Martínez", 
    "Lucía Rodríguez", "David Sánchez", "Sofía Fernández", "Pablo González",
    "Elena Ruiz", "Javier Díaz", "Carmen Moreno", "Alejandro Muñoz",
    "Laura Álvarez", "Daniel Romero", "Paula Torres", "Manuel Navarro",
    "Isabel Jiménez", "Miguel Gil", "Marta Serrano", "Antonio Molina"
]

# Preguntas y posibles respuestas (correctas e incorrectas)
EXAM_QUESTIONS = [
    {
        "q": "Resuelve: 2x + 4 = 12",
        "correct": "x = 4",
        "wrong": ["x = 3", "x = 8", "x = 6", "No tiene solución"]
    },
    {
        "q": "Derivada de f(x) = x^2",
        "correct": "2x",
        "wrong": ["x", "2", "x^3/3", "0"]
    },
    {
        "q": "Integral de 3dx",
        "correct": "3x + C",
        "wrong": ["3", "x + C", "3x", "0"]
    },
    {
        "q": "Matriz Identidad 2x2",
        "correct": "[[1,0],[0,1]]",
        "wrong": ["[[0,1],[1,0]]", "[[1,1],[1,1]]", "[[0,0],[0,0]]"]
    },
    {
        "q": "Valor de pi (aprox)",
        "correct": "3.1416",
        "wrong": ["3.15", "3.14", "3.00", "2.71"]
    }
]

def get_connection():
    conn_str = f'DRIVER={driver};SERVER={server};PORT=1433;DATABASE={database};UID={username};PWD={password};Encrypt=yes;TrustServerCertificate=yes'
    try:
        return pyodbc.connect(conn_str)
    except Exception as e:
        print(f"❌ Error conectando a Azure: {e}")
        return None

def send_signalr_broadcast(message_text):
    conn_str = os.getenv("AZURE_SIGNALR_CONNECTION_STRING")
    if not conn_str:
        return
    try:
        endpoint = conn_str.split(";")[0].replace("Endpoint=", "")
        access_key = conn_str.split(";")[1].replace("AccessKey=", "")
        hub_name = "olimpiada_hub"
        api_url = f"{endpoint}/api/v1/hubs/{hub_name}"
        
        payload = {"iat": int(time.time()), "exp": int(time.time()) + 3600, "aud": api_url}
        token = jwt.encode(payload, access_key, algorithm="HS256")
        
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        data = {"target": "*", "arguments": [message_text]}
        requests.post(api_url, json=data, headers=headers)
    except:
        pass

def insert_student_activity(cursor):
    # Simular que un alumno responde una pregunta
    name = random.choice(STUDENTS)
    question_data = random.choice(EXAM_QUESTIONS)
    exercise_name = question_data["q"]
    
    # 70% de probabilidad de acertar
    is_correct_val = 1 if random.random() > 0.3 else 0
    
    if is_correct_val == 1:
        student_answer = question_data["correct"]
        score = 100
    else:
        student_answer = random.choice(question_data["wrong"])
        score = 0
    
    exam_date = datetime.now()

    # Insertar en BD
    query = """
    INSERT INTO Students (Name, Subject, Score, ExamDate, ExerciseName, IsCorrect, StudentAnswer) 
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    cursor.execute(query, (name, CURRENT_SUBJECT, score, exam_date, exercise_name, is_correct_val, student_answer))
    
    status_icon = "✅" if is_correct_val else "❌"
    print(f"📝 {name} | {exercise_name} | Resp: {student_answer} {status_icon}")
    
    send_signalr_broadcast(f"Update: {name} ha respondido '{exercise_name}'")

def start_simulation():
    print(f"--- 🏫 EXAMEN EN CURSO: {CURRENT_SUBJECT} ---")
    print(f"Tema: {EXAM_TOPIC}")
    print("----------------------------------------------")

    conn = get_connection()
    if not conn: return

    cursor = conn.cursor()

    try:
        while True:
            insert_student_activity(cursor)
            conn.commit()
            time.sleep(random.uniform(1.0, 3.0)) # Ritmo de examen

    except KeyboardInterrupt:
        print("\n🛑 Examen finalizado.")
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    start_simulation()