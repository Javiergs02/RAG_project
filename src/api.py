import os
import shutil
import json
import chromadb
import ollama
from datetime import datetime
from typing import List
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel


# Importamos las herramientas de ingesta que configuraremos en ingesta.py
from src.ingesta import procesar_documentos_y_crear_chunks, get_embedding_function

app = FastAPI(title="Motor RAG de Sesión", version="2.0")

# 1. Configuración de persistencia y cliente ChromaDB
CHROMA_PATH = "db_local/chroma_data"
COLLECTION_NAME = "documentos_sesion"

chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
embedding_fn = get_embedding_function()

# Modelos Pydantic para tipado de peticiones
class QueryRequest(BaseModel):
    pregunta: str

class QueryResponse(BaseModel):
    respuesta: str
    fuentes: List[str]

class FeedbackRequest(BaseModel):
    pregunta: str
    respuesta: str
    fuentes: List[str]
    valoracion: int  # 1 para 👍, 0 para 👎


# --- ENDPOINT 1: ESTADO DEL SISTEMA ---
@app.get("/status")
async def get_status():
    try:
        coleccion = chroma_client.get_collection(name=COLLECTION_NAME, embedding_function=embedding_fn)
        total_chunks = coleccion.count()
        return {"status": "ready", "chunks_activos": total_chunks}
    except Exception:
        return {"status": "empty", "chunks_activos": 0}


# --- ENDPOINT 2: SUBIDA Y REEMPLAZO (SESIÓN) ---
@app.post("/upload")
async def upload_y_reemplazar(files: List[UploadFile] = File(...)):
    try:
        upload_dir = "data/manuales_sesion"
        if os.path.exists(upload_dir):
            shutil.rmtree(upload_dir)
        os.makedirs(upload_dir, exist_ok=True)

        rutas_guardadas = []
        for file in files:
            ruta_destino = os.path.join(upload_dir, file.filename)
            with open(ruta_destino, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            rutas_guardadas.append(ruta_destino)

        # Resetear colección previa en ChromaDB
        try:
            chroma_client.delete_collection(name=COLLECTION_NAME)
        except Exception:
            pass

        coleccion = chroma_client.create_collection(
            name=COLLECTION_NAME,
            embedding_function=embedding_fn,
            metadata={"hnsw:space": "cosine"}
        )

        # Trocear y extraer texto
        chunks, metadatas, ids = procesar_documentos_y_crear_chunks(rutas_guardadas)

        if not chunks:
            raise HTTPException(status_code=400, detail="No se pudo extraer texto legible de los PDFs.")

        # Insertar en ChromaDB (la función embedding_fn calcula los vectores automáticamente)
        coleccion.add(
            documents=chunks,
            metadatas=metadatas,
            ids=ids
        )

        return {
            "status": "success",
            "archivos_procesados": [f.filename for f in files],
            "total_chunks": len(chunks)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en la ingesta: {str(e)}")


# --- ENDPOINT 3: CONSULTA AL MOTOR RAG ---
@app.post("/query", response_model=QueryResponse)
async def consultar_rag(request: QueryRequest):
    try:
        # Verificar que la colección existe y tiene datos
        try:
            coleccion = chroma_client.get_collection(name=COLLECTION_NAME, embedding_function=embedding_fn)
        except Exception:
            raise HTTPException(status_code=400, detail="No hay documentos activos. Por favor, sube un PDF primero.")

        if coleccion.count() == 0:
            raise HTTPException(status_code=400, detail="La sesión actual está vacía.")

        # 1. Recuperar los fragmentos más relevantes (Top-K)
        resultados = coleccion.query(
            query_texts=[request.pregunta],
            n_results=3
        )

        documentos_recuperados = resultados["documents"][0]
        metadatos_recuperados = resultados["metadatas"][0]

        contexto = "\n\n---\n\n".join(documentos_recuperados)
        fuentes_unicas = list({m.get("source", "Documento desconocido") for m in metadatos_recuperados})

        # 2. Construir el prompt para Llama 3.2
        prompt_sistema = (
            "Eres un asistente técnico especializado. Responde a la pregunta del usuario "
            "utilizando ÚNICAMENTE la siguiente información de contexto. Si la respuesta "
            "no se encuentra en el contexto, indica amablemente que no dispones de esa información.\n\n"
            f"CONTEXTO:\n{contexto}"
        )

        # 3. Llamar a Ollama (Llama 3.2)
        # Nota: Si Ollama corre en el host, la URL suele ser host.docker.internal:11434
        cliente_ollama = ollama.Client(host=os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434"))
        
        respuesta_llm = cliente_ollama.chat(
            model="llama3.2",
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": request.pregunta}
            ]
        )

        return QueryResponse(
            respuesta=respuesta_llm["message"]["content"],
            fuentes=fuentes_unicas
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando respuesta: {str(e)}")

@app.post("/feedback")
async def registrar_feedback(req: FeedbackRequest):
    try:
        os.makedirs("data/logs", exist_ok=True)
        ruta_log = "data/logs/interacciones.jsonl"
        with open(ruta_log, "a", encoding="utf-8") as f:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "pregunta": req.pregunta,
                "respuesta": req.respuesta,
                "fuentes": req.fuentes,
                "valoracion": req.valoracion
            }
            f.write(json.dumps(log_entry) + "\n")
            
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error guardando log: {str(e)}")