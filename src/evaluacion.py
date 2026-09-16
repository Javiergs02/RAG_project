import json
from datasets import Dataset
from ragas import evaluate
from ragas.run_config import RunConfig
from ragas.metrics import faithfulness, answer_relevancy, context_precision
from langchain_community.chat_models import ChatOllama
from langchain_community.embeddings import HuggingFaceEmbeddings

# Importamos tu función de la Fase 2 (asegúrate de que rag_pipeline.py esté en la misma carpeta)
from rag_pipeline import recuperar_contexto, generar_respuesta

def cargar_dataset(ruta="data/evaluacion/eval_dataset.json"):
    with open(ruta, 'r', encoding='utf-8') as f:
        return json.load(f)

def preparar_datos_para_ragas(datos_json):
    print("🤖 Ejecutando el RAG para generar respuestas sobre el dataset de prueba...")
    preguntas = []
    respuestas = []
    contextos = []
    ground_truths = []

    for item in datos_json:
        pregunta = item["question"]
        print(f"Procesando: {pregunta}")
        
        # Ejecutamos tu sistema actual
        texto_contexto, fuentes = recuperar_contexto(pregunta)
        respuesta_llm = generar_respuesta(pregunta, texto_contexto)
        
        preguntas.append(pregunta)
        respuestas.append(respuesta_llm)
        # Ragas espera una lista de strings para el contexto
        contextos.append([texto_contexto]) 
        ground_truths.append(item["ground_truth"])

    # Formato exacto que requiere la librería Datasets de HuggingFace
    data_dict = {
        "question": preguntas,
        "answer": respuestas,
        "contexts": contextos,
        "ground_truth": ground_truths
    }
    return Dataset.from_dict(data_dict)

def evaluar_rag(dataset):
    print("\n⚖️ Iniciando evaluación matemática con Ragas (LLM-as-a-judge)...")
    
    # Añadimos temperature=0 para que las evaluaciones no varíen
    juez_llm = ChatOllama(
        model="llama3.2", 
        base_url="http://host.docker.internal:11434",
        temperature=0 ,
        format="json" 
    )
    juez_embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    # CRÍTICO: Evitar atascos en Ollama limitando la concurrencia
    config = RunConfig(timeout=300, max_workers=1)

    # Lanzamos la evaluación con la nueva configuración
    resultados = evaluate(
        dataset=dataset,
        metrics=[faithfulness, answer_relevancy, context_precision],
        llm=juez_llm,
        embeddings=juez_embeddings,
        run_config=config
    )
    
    return resultados

if __name__ == "__main__":
    datos_prueba = cargar_dataset()
    dataset_huggingface = preparar_datos_para_ragas(datos_prueba)
    
    metricas = evaluar_rag(dataset_huggingface)
    
    print("\n" + "="*50)
    print("📊 RESULTADOS DE LA EVALUACIÓN:")
    print("="*50)
    print(metricas)
    
    # Opcional: Exportar a CSV para adjuntar al repositorio de GitHub
    df = metricas.to_pandas()
    df.to_csv("db_local/resultados/resultados_evaluacion.csv", index=False)
    print("\n✅ Resultados detallados guardados en 'resultados_evaluacion.csv'")