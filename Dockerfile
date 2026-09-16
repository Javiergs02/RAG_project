FROM python:3.11-slim

# Evitar que Python genere archivos .pyc y forzar que los prints salgan en consola sin retraso
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar herramientas de compilación del sistema (necesarias para algunas librerías de ML)
RUN apt-get update && apt-get install -y build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del código
COPY . .