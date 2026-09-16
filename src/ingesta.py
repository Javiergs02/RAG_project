import fitz  # PyMuPDF: Excelente para extraer texto real y metadatos
from sentence_transformers import SentenceTransformer
import chromadb

def extraer_y_fragmentar(pdf_path, chunk_size=1000, overlap=200):
    print(f"1. Extrayendo texto de {pdf_path}...")
    doc = fitz.open(pdf_path)
    chunks_con_metadatos = []
    
    for num_pagina, pagina in enumerate(doc, start=1):
        texto_pagina = pagina.get_text()
        
        # Limpieza básica
        texto_limpio = texto_pagina.replace('\n', ' ').strip()
        if not texto_limpio:
            continue
            
        # Chunking manual con solapamiento
        inicio = 0
        while inicio < len(texto_limpio):
            fin = inicio + chunk_size
            chunk_texto = texto_limpio[inicio:fin]
            
            # Guardamos el texto junto a su origen exacto
            chunks_con_metadatos.append({
                "texto": chunk_texto,
                "metadata": {
                    "source": pdf_path.split('/')[-1],
                    "page": num_pagina
                }
            })
            inicio += (chunk_size - overlap)
            
    print(f"Generados {len(chunks_con_metadatos)} chunks con trazabilidad.")
    return chunks_con_metadatos

def crear_vector_db(chunks, db_path="db_local/chroma_data"):
    print("2. Cargando modelo de embeddings (Baseline)...")
    # Usamos el baseline recomendado para poder medir mejoras luego
    modelo = SentenceTransformer('all-MiniLM-L6-v2')
    
    print("3. Vectorizando e indexando en ChromaDB...")
    cliente_chroma = chromadb.PersistentClient(path=db_path)
    coleccion = cliente_chroma.get_or_create_collection(name="manuales_medicos")
    
    # Preparamos los datos para Chroma
    documentos = [c["texto"] for c in chunks]
    metadatos = [c["metadata"] for c in chunks]
    ids = [f"chunk_{i}" for i in range(len(chunks))]
    
    # Generamos los embeddings directamente con el modelo
    embeddings = modelo.encode(documentos).tolist()
    
    coleccion.add(
        documents=documentos,
        embeddings=embeddings,
        metadatas=metadatos,
        ids=ids
    )
    print("Base de datos indexada correctamente.")
    return coleccion, modelo

def buscar_con_fuentes(coleccion, modelo, query, top_k=3):
    print(f"\n--- Búsqueda: '{query}' ---")
    query_embedding = modelo.encode([query]).tolist()
    
    resultados = coleccion.query(
        query_embeddings=query_embedding,
        n_results=top_k
    )
    
    # Formateamos la salida para ver claramente el texto y su fuente
    for i in range(top_k):
        texto = resultados['documents'][0][i]
        meta = resultados['metadatas'][0][i]
        distancia = resultados['distances'][0][i] # Útil para ver la similitud matemática
        
        print(f"\n🔹 Resultado {i+1} (Similitud: {distancia:.4f})")
        print(f"📍 Fuente: {meta['source']} - Página: {meta['page']}")
        print(f"📝 Texto: {texto[:200]}...")

if __name__ == "__main__":
    # Asegúrate de tener un PDF de prueba, por ejemplo el de un simulador médico
    ruta_pdf = "data/manuales/manual_prueba.pdf"
    
    # Ejecución del pipeline
    chunks = extraer_y_fragmentar(ruta_pdf)
    coleccion, modelo = crear_vector_db(chunks)
    
    # Prueba del MVP
    buscar_con_fuentes(coleccion, modelo, "¿Cuáles son las especificaciones técnicas?")