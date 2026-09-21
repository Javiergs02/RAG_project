
```markdown
# 🏥 Asistente RAG Dinámico para Documentación Técnica

Sistema **RAG (Retrieval-Augmented Generation)** contenerizado y basado en sesiones, diseñado específicamente para la consulta interactiva y el análisis de manuales técnicos y documentación médica. Su arquitectura prioriza la precisión documental, la trazabilidad estricta y la total privacidad de los datos mediante inferencia local.

---

## 🚀 ¿Por qué este proyecto en lugar de usar un LLM base (ej. Ollama directo)?

Interactuar directamente con un modelo de lenguaje (como Llama 3.2) presenta limitaciones críticas en entornos profesionales. Este proyecto transforma al LLM de un "oráculo de memoria" a un **"analista a libro abierto"** mediante los siguientes pilares técnicos:

1. **Eliminación de Alucinaciones (Grounding):** Los modelos base tienden a inventar especificaciones cuando no disponen de datos exactos. Nuestra arquitectura intercepta la consulta, extrae los fragmentos pertinentes de los manuales mediante búsqueda vectorial y restringe al modelo para que responda *única y exclusivamente* basándose en esa evidencia.
2. **Trazabilidad y Auditoría de Fuentes:** Un LLM estándar no puede justificar el origen de su información. Este sistema mapea cada respuesta con los metadatos de ChromaDB, indicando de forma explícita **el archivo PDF y el número de página exactos** de donde se extrajo el contenido.
3. **Privacidad y Cero Fugas de Datos (Zero-Data Leak):** Diseñado para operar íntegramente en entornos locales (vía Docker y Ollama). Ningún documento confidencial, manual técnico o interacción privada sale hacia servidores de terceros.
4. **Arquitectura Dinámica por Sesiones:** A diferencia de las bases de conocimiento estáticas y monolíticas, este sistema implementa un patrón de limpieza y sustitución del espacio vectorial por sesión, evitando la contaminación cruzada de datos entre diferentes manuales o equipos.
5. **Telemetría y Evaluación Continua:** Incorpora un sistema de retroalimentación de usuario integrado (valoraciones de acierto) que registra automáticamente las interacciones en un histórico en formato JSONL, sentando las bases para una auditoría de rendimiento posterior mediante pipelines de evaluación cuantitativa (ej. con Ragas).

---

## 🛠️ Stack Tecnológico

* **Frontend:** Streamlit (Interfaz conversacional, gestión de subida de archivos y widgets de feedback).
* **Backend:** FastAPI (Microservicio de orquestación, endpoints REST y gestión de flujos).
* **Base de Datos Vectorial:** ChromaDB (Persistencia espacial y recuperación por similitud de coseno).
* **Embeddings:** SentenceTransformers (`all-MiniLM-L6-v2`).
* **Motor de Inferencia (LLM):** Llama 3.2 (Ejecución local mediante Ollama).
* **Orquestación y Contenerización:** Docker & Docker Compose.

---

## 📂 Estructura del Repositorio

```text
/RAG_project
├── data/
│   ├── evaluacion/       # Datasets para pruebas fuera de línea
│   ├── logs/             # Histórico de telemetría e interacciones (.jsonl)
│   ├── manuales/         # Repositorio base de documentación
│   └── manuales_sesion/  # Archivos dinámicos de la sesión actual
├── db_local/             # Persistencia de volúmenes de ChromaDB
├── src/
│   ├── api.py            # Servidor FastAPI (Orquestación RAG y endpoints)
│   ├── app.py            # Interfaz gráfica de Streamlit
│   └── ingesta.py         # Pipeline de PyMuPDF, fragmentación (chunking) y embeddings
├── .dockerignore
├── .gitignore
├── Dockerfile
├── docker-compose.yml
└── README.md

```

---

## ⚙️ Guía de Despliegue e Instalación

### Requisitos Previos

* Tener instalado **Docker** y **Docker Compose (V2)**.
* Tener instalado **Ollama** en la máquina host con el modelo base descargado:
```bash
ollama run llama3.2

```



### Puesta en Marcha

1. Clona este repositorio en tu entorno local (o WSL/Ubuntu):
```bash
git clone <url-del-repositorio>
cd RAG_project

```


2. Construye y levanta los contenedores en segundo plano:
```bash
docker compose up -d --build

```


3. Accede a la interfaz web de usuario:
Abre tu navegador e introduce la URL: **`http://localhost:8501`**.

### Modo de Uso

* **Carga documental:** Utiliza el panel lateral izquierdo en Streamlit para seleccionar y subir uno o varios manuales en formato PDF.
* **Indexación:** Haz clic en el botón de indexación para activar el pipeline de fragmentación y vectorización en ChromaDB.
* **Consulta interactiva:** Realiza tus preguntas técnicas en el chat principal y despliega el acordeón de fuentes para verificar la trazabilidad exacta de cada respuesta. Valida los resultados utilizando los botones de feedback inferiores.

```

```