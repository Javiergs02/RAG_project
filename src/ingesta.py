import fitz  # PyMuPDF
import chromadb
# Importamos la función nativa de ChromaDB para integrar modelos de SentenceTransformers
import chromadb.utils.embedding_functions as embedding_functions

# --- 1. MODELO DE EMBEDDINGS COMPATIBLE CON CHROMADB ---
def get_embedding_function():
    """
    Devuelve la función de embeddings configurada para que ChromaDB 
    vectorice automáticamente los textos al insertarlos o consultarlos.
    """
    return embedding_functions.SentenceTransformerEmbeddingFunction(model_name='all-MiniLM-L6-v2')

# --- 2. LÓGICA ORIGINAL DE EXTRACCIÓN (Intacta) ---
def extraer_y_fragmentar(pdf_path, chunk_size=1000, overlap=200):
    print(f"Extrayendo texto de {pdf_path}...")
    doc = fitz.open(pdf_path)
    chunks_con_metadatos = []
    
    for num_pagina, pagina in enumerate(doc, start=1):
        texto_pagina = pagina.get_text()
        
        texto_limpio = texto_pagina.replace('\n', ' ').strip()
        if not texto_limpio:
            continue
            
        inicio = 0
        while inicio < len(texto_limpio):
            fin = inicio + chunk_size
            chunk_texto = texto_limpio[inicio:fin]
            
            chunks_con_metadatos.append({
                "texto": chunk_texto,
                "metadata": {
                    "source": pdf_path.split('/')[-1],
                    "page": num_pagina
                }
            })
            inicio += (chunk_size - overlap)
            
    print(f"-> Generados {len(chunks_con_metadatos)} chunks de {pdf_path.split('/')[-1]}.")
    return chunks_con_metadatos

# --- 3. NUEVO PUENTE PARA FASTAPI (Procesa múltiples archivos) ---
def procesar_documentos_y_crear_chunks(rutas_pdf):
    """
    Recibe una lista de rutas PDF y devuelve tres listas separadas (documentos, metadatos, ids)
    tal y como lo requiere la función collection.add() de ChromaDB.
    """
    todos_los_documentos = []
    todos_los_metadatos = []
    todos_los_ids = []
    
    chunk_global_id = 0
    
    for ruta in rutas_pdf:
        # Reutilizamos tu función original por cada PDF subido
        chunks_diccionarios = extraer_y_fragmentar(ruta)
        
        for chunk in chunks_diccionarios:
            todos_los_documentos.append(chunk["texto"])
            todos_los_metadatos.append(chunk["metadata"])
            todos_los_ids.append(f"chunk_{chunk_global_id}")
            chunk_global_id += 1
            
    return todos_los_documentos, todos_los_metadatos, todos_los_ids

# --- 4. MODO PRUEBA LOCAL (Para ejecutar desde consola si lo necesitas) ---
if __name__ == "__main__":
    # Prueba rápida sin necesidad de levantar FastAPI
    ruta_pdf = "data/manuales/manual_prueba.pdf"