# 🏥 Asistente Médico RAG: Inteligencia Artificial para Simuladores Clínicos

Este proyecto es un sistema de Recuperación Aumentada (RAG) diseñado para consultar manuales técnicos de simuladores médicos de alta fidelidad. Permite a los usuarios obtener respuestas precisas, basadas **exclusivamente** en la documentación oficial, eliminando el riesgo de alucinaciones (Zero-Data-Leak).


## 🚀 Tecnologías Principales

- **Motor LLM:** Llama 3.2 (ejecutado en local vía Ollama para máxima privacidad)
- **Base de Datos Vectorial:** ChromaDB
- **Backend / API:** FastAPI + Uvicorn
- **Frontend:** Streamlit
- **Evaluación:** Framework Ragas
- **Infraestructura:** Docker & Docker Compose

## 🏗️ Arquitectura del Sistema (Clean Architecture)

El proyecto está diseñado bajo una arquitectura de microservicios, separando claramente la persistencia, la lógica de negocio y la interfaz de usuario:

```text
mi-proyecto-rag/
├── data/                   # Documentación cruda y datasets de prueba
├── db_local/               # Base de datos vectorial (ChromaDB) y métricas
├── src/                    # Código fuente (API, Frontend, Ingesta, RAG Pipeline)
├── docker-compose.yml      # Orquestación de contenedores
└── requirements.txt        # Dependencias de Python

## ⚙️ Instalación y Despliegue Rápido

### Prerrequisitos (Paso Cero)
Antes de arrancar el proyecto, asegúrate de tener instalado en tu sistema:
1. **Docker y Docker Compose**.
2. **Ollama** (para la ejecución del LLM en local).
3. Haber descargado el modelo Llama 3.2 en tu máquina ejecutando en tu terminal:
   ```bash
   ollama pull llama3.2

Despliegue del Ecosistema
1. Clonar el repositorio y preparar los datos
Clona este repositorio y coloca tus manuales de los simuladores en formato PDF dentro de la carpeta data/manuales/.

2. Poblar la base de datos vectorial
Ejecuta el script de ingesta para fragmentar y vectorizar los manuales:

Bash
python src/ingesta.py

3. Levantar la infraestructura
Despliega la API y la interfaz gráfica usando Docker Compose:

Bash
docker compose up -d --build

4. Uso de la plataforma

Interfaz de Chat (Streamlit): Abre tu navegador en http://localhost:8501

Documentación de la API (Swagger): Disponible en http://localhost:8000/docs
