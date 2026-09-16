import chromadb
from sentence_transformers import SentenceTransformer
import requests
import json

def recuperar_contexto(query, db_path="db_local/chroma_data", top_k=3):
    # 1. Cargamos la BD y el modelo que ya creamos en la Fase 1
    cliente_chroma = chromadb.PersistentClient(path=db_path)
    coleccion = cliente_chroma.get_collection(name="manuales_medicos")
    modelo = SentenceTransformer('all-MiniLM-L6-v2')
    
    # 2. Buscamos los fragmentos
    query_embedding = modelo.encode([query]).tolist()
    resultados = coleccion.query(query_embeddings=query_embedding, n_results=top_k)
    
    # 3. Formateamos el contexto y guardamos las fuentes
    contextos = []
    fuentes = []
    
    for i in range(top_k):
        texto = resultados['documents'][0][i]
        meta = resultados['metadatas'][0][i]
        contextos.append(texto)
        fuentes.append(f"{meta['source']} (Pág. {meta['page']})")
        
    return "\n\n---\n\n".join(contextos), fuentes

def generar_respuesta(query, contexto):
    # 4. El Prompt de un AI Engineer (Estricto y guiado)
    prompt = f"""
    Eres un asistente técnico especializado en simuladores médicos.
    Utiliza ÚNICAMENTE el siguiente contexto para responder a la pregunta. 
    Si la respuesta no está en el contexto, responde "No encuentro información suficiente en los manuales proporcionados."
    
    CONTEXTO EXTRAÍDO:
    {contexto}
    
    PREGUNTA DEL USUARIO: 
    {query}
    """

    # 5. Llamada directa a la API de Ollama
    url = "http://host.docker.internal:11434/api/generate"
    payload = {
        "model": "llama3.2",
        "prompt": prompt,
        "stream": False # Para recibir toda la respuesta de golpe en esta prueba
    }

    print("🧠 Generando respuesta con Llama 3.2 (Ollama)...")
    respuesta = requests.post(url, json=payload)
    
    if respuesta.status_code == 200:
        return respuesta.json()["response"]
    else:
        return f"Error en Ollama: {respuesta.text}"

if __name__ == "__main__":
    pregunta = "¿Qué precauciones de temperatura debo tener con el simulador?"
    
    print(f"🔎 Buscando información para: '{pregunta}'")
    contexto, fuentes = recuperar_contexto(pregunta)
    
    respuesta_llm = generar_respuesta(pregunta, contexto)
    
    print("\n" + "="*50)
    print("🤖 RESPUESTA DEL SISTEMA RAG:")
    print("="*50)
    print(respuesta_llm)
    print("\n📚 FUENTES UTILIZADAS:")
    for fuente in set(fuentes): # Usamos set() para no repetir fuentes si coge 2 párrafos de la misma página
        print(f"- {fuente}")