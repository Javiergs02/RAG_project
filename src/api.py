from fastapi import FastAPI
from pydantic import BaseModel
from src.rag_pipeline import recuperar_contexto, generar_respuesta

# Inicializamos la API
app = FastAPI(
    title="API - RAG Médico",
    description="Motor de búsqueda y generación sobre manuales de simuladores",
    version="1.0"
)

# Definimos la estructura de los datos que espera recibir la API
class QueryRequest(BaseModel):
    pregunta: str

@app.post("/ask")
def resolver_duda(request: QueryRequest):
    print(f"📩 Petición recibida: {request.pregunta}")
    
    # 1. Recuperación
    contexto, fuentes = recuperar_contexto(request.pregunta)
    
    # 2. Generación
    respuesta = generar_respuesta(request.pregunta, contexto)
    
    # 3. Limpieza de fuentes (evitamos duplicados si saca 2 chunks de la misma página)
    fuentes_unicas = list(set(fuentes))
    
    # 4. Devolvemos un JSON estructurado
    return {
        "answer": respuesta,
        "sources": fuentes_unicas
    }

@app.get("/")
def health_check():
    return {"status": "El motor RAG está funcionando correctamente."}