# Usar una imagen base ligera de Python 3.12 (Debian Bookworm)
FROM python:3.12-slim

# Evitar archivos .pyc y buffer de salida
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# 1. Instalar dependencias del sistema necesarias para ODBC 18 y compilación
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg2 \
    unixodbc-dev \
    build-essential \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 2. Instalar Microsoft ODBC Driver 18 for SQL Server
RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && curl https://packages.microsoft.com/config/debian/12/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
    && rm -rf /var/lib/apt/lists/*

# 3. Copiar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copiar el código de la aplicación
COPY . .

# 5. Configuración de Entorno para Streamlit y Azure
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_ENABLE_CORS=false
ENV STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false

# 6. Exponer el puerto
EXPOSE 8501

# 7. REMOVED HEALTHCHECK to avoid conflicts with Azure Probe
# Azure will ping the port automatically.

# 8. Comando de inicio (Usando variables de entorno donde sea posible)
ENTRYPOINT ["streamlit", "run", "app.py"]
