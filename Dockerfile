# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar herramientas de compilación del sistema
RUN apt-get update && apt-get install -y build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Usamos la caché interna de pip en lugar de descartarla
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

COPY . .