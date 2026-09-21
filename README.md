# Dynamic Multi-Document RAG Assistant

A containerized **Retrieval-Augmented Generation (RAG)** system that allows users to upload one or more PDF documents, build a temporary semantic knowledge base, and interact with the documents through a conversational interface.

The system combines **semantic vector retrieval** with a locally hosted **Llama 3.2** model to generate responses grounded in the uploaded documentation. Retrieved sources are preserved at document and page level to improve answer traceability.

---

## Overview

Large Language Models can generate fluent answers, but they do not automatically have access to private or domain-specific documents.

This project addresses that problem by implementing a complete RAG pipeline:

```text
                    PDF DOCUMENTS
                          │
                          ▼
                  ┌───────────────┐
                  │   PyMuPDF     │
                  │ Text Extract  │
                  └───────┬───────┘
                          │
                          ▼
                  ┌───────────────┐
                  │    Chunking   │
                  └───────┬───────┘
                          │
                          ▼
                  ┌────────────────────┐
                  │ SentenceTransformers│
                  │  all-MiniLM-L6-v2  │
                  └─────────┬──────────┘
                            │
                       Embeddings
                            │
                            ▼
                     ┌────────────┐
                     │  ChromaDB  │
                     │ Vector DB  │
                     └─────┬──────┘
                           │
                    Semantic Retrieval
                           │
                           ▼
                    Relevant Chunks
                           │
                           ▼
                     ┌────────────┐
                     │  Llama 3.2 │
                     │   Ollama   │
                     └─────┬──────┘
                           │
                           ▼
                  Grounded Response
                    + Source Metadata
```

The embedding model and the language model serve different purposes:

* **Embedding model:** converts document chunks and user queries into vector representations used for semantic retrieval.
* **ChromaDB:** compares the query embedding with stored embeddings and retrieves the most relevant document chunks.
* **Llama 3.2:** receives the retrieved text together with the user's question and generates the final response.

---

## Key Features

### 📄 Dynamic PDF Ingestion

Users can upload one or multiple PDF documents directly through the Streamlit interface.

The system automatically:

1. Extracts text from the PDFs.
2. Splits the text into overlapping chunks.
3. Generates vector embeddings.
4. Stores the embeddings and metadata in ChromaDB.
5. Makes the documents immediately available for querying.

This removes the need to manually modify the source code when adding new documentation.

---

### 🔎 Semantic Retrieval

The system uses:

**`all-MiniLM-L6-v2`**

to generate embeddings for both documents and user queries.

Instead of relying exclusively on keyword matching, the vector database performs similarity-based retrieval to identify chunks that are semantically related to the question.

The current implementation retrieves the **top 3 most relevant chunks**.

---

### 🤖 Local LLM Inference

Response generation is handled by:

**Llama 3.2 + Ollama**

The LLM runs locally rather than relying on a hosted inference API.

This architecture is particularly useful for environments where documents may contain sensitive or proprietary information and local processing is preferred.

> Local inference reduces the need to transmit documents and queries to external model providers, although deployment security and infrastructure configuration must still be considered separately.

---

### 📚 Source Traceability

Each document chunk is stored together with metadata including:

```text
source → PDF filename
page   → PDF page number
```

Retrieved sources are returned alongside the generated answer, allowing users to identify which documents contributed to the response.

---

### 🔄 Session-Based Knowledge Base

Each document upload creates a new session knowledge base.

When a new set of PDFs is uploaded:

```text
Previous documents
       ↓
Vector collection reset
       ↓
New PDFs processed
       ↓
New embeddings generated
       ↓
New ChromaDB collection
```

This prevents documents from previous sessions from being unintentionally mixed with the current document set.

The current implementation is therefore designed around **single-session knowledge isolation**, rather than persistent multi-user document management.

---

### 👍 User Feedback and Interaction Logging

Users can provide positive or negative feedback on generated responses.

Interactions are stored in JSONL format:

```json
{
  "timestamp": "...",
  "pregunta": "...",
  "respuesta": "...",
  "fuentes": ["document.pdf"],
  "valoracion": 1
}
```

This provides a foundation for analysing real interactions and identifying retrieval or generation failures.

---

### 📊 Evaluation

The repository includes a dataset for offline evaluation of the RAG pipeline.

The evaluation framework is designed to measure aspects such as:

* **Faithfulness**
* **Answer Relevancy**
* **Context Precision**
* **Context Recall**

The evaluation dataset can be expanded as the system evolves, allowing different retrieval and chunking strategies to be compared quantitatively.

---

## Technology Stack

| Component        | Technology           | Purpose                                 |
| ---------------- | -------------------- | --------------------------------------- |
| Frontend         | Streamlit            | Document upload and conversational UI   |
| Backend          | FastAPI              | REST API and RAG orchestration          |
| PDF Processing   | PyMuPDF              | Text extraction                         |
| Embeddings       | SentenceTransformers | Semantic vector generation              |
| Embedding Model  | `all-MiniLM-L6-v2`   | Document/query embeddings               |
| Vector Database  | ChromaDB             | Vector storage and similarity retrieval |
| LLM              | Llama 3.2            | Response generation                     |
| Local Inference  | Ollama               | Local LLM serving                       |
| Containerization | Docker               | Reproducible deployment                 |
| Orchestration    | Docker Compose       | Multi-container application             |
| Evaluation       | Ragas                | RAG evaluation                          |

---

## Architecture

The application follows a containerized client-server architecture:

```text
┌─────────────────────────────────────────────────────────┐
│                    User / Browser                       │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                 Streamlit Frontend                      │
│                                                         │
│  • PDF upload                                           │
│  • Chat interface                                       │
│  • Source display                                       │
│  • User feedback                                        │
└─────────────────────────┬───────────────────────────────┘
                          │ HTTP
                          ▼
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Backend                      │
│                                                         │
│  /status                                                │
│  /upload                                                │
│  /query                                                 │
│  /feedback                                              │
└───────────────┬─────────────────────────┬───────────────┘
                │                         │
                ▼                         ▼
       ┌─────────────────┐       ┌─────────────────┐
       │    ChromaDB     │       │     Ollama      │
       │                 │       │                 │
       │ Vector Storage  │       │   Llama 3.2     │
       │ + Retrieval     │       │ Local Inference │
       └─────────────────┘       └─────────────────┘
```

### Query Pipeline

When a user asks a question:

```text
User Question
      │
      ▼
Embedding Model
      │
      ▼
Query Embedding
      │
      ▼
ChromaDB Similarity Search
      │
      ▼
Top-K Relevant Chunks
      │
      ▼
Prompt Construction
      │
      ▼
Llama 3.2
      │
      ▼
Answer + Retrieved Sources
```

The LLM does not directly search the vector database. The retrieval layer first identifies relevant document chunks, which are then provided to the LLM as contextual evidence.

---

## Project Structure

```text
RAG_project/
│
├── data/
│   ├── evaluacion/
│   │   └── eval_dataset.json
│   │
│   ├── logs/
│   │   └── interacciones.jsonl
│   │
│   ├── manuales/
│   │   └── .gitkeep
│   │
│   └── manuales_sesion/
│       └── ...
│
├── src/
│   ├── api.py
│   ├── app.py
│   └── ingesta.py
│
├── .dockerignore
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

### Main Components

#### `src/api.py`

FastAPI backend responsible for:

* Document upload
* Session knowledge-base creation
* ChromaDB management
* Semantic retrieval
* Llama 3.2 inference
* Source metadata handling
* User feedback logging

#### `src/ingesta.py`

Document ingestion pipeline responsible for:

* PDF text extraction
* Text cleaning
* Chunk generation
* Metadata creation
* Embedding configuration

#### `src/app.py`

Streamlit frontend responsible for:

* PDF upload
* Session status
* Conversational interface
* Source visualization
* User feedback

---

## RAG Ingestion Pipeline

When PDFs are uploaded, the system processes them as follows:

```text
PDF
 │
 ▼
PyMuPDF
 │
 ▼
Extracted Text
 │
 ▼
Text Cleaning
 │
 ▼
1000-character chunks
with 200-character overlap
 │
 ▼
SentenceTransformer
 │
 ▼
Embeddings
 │
 ▼
ChromaDB
```

Each chunk is stored together with metadata:

```python
{
    "source": "document.pdf",
    "page": 12
}
```

This metadata is later used to identify the source of retrieved information.

---

## Retrieval and Generation

For each user query:

1. The question is converted into an embedding.
2. ChromaDB performs similarity search against the stored document embeddings.
3. The three most relevant chunks are retrieved.
4. The retrieved text is inserted into the LLM prompt.
5. Llama 3.2 generates a response based on the supplied context.
6. The associated document sources are returned to the frontend.

The system prompt explicitly instructs the model to avoid using information outside the retrieved context and to acknowledge when the available context does not contain the requested information.

This is intended to **reduce unsupported generation**, rather than guarantee the complete elimination of hallucinations.

---

## Installation

### Requirements

* Docker
* Docker Compose V2
* Ollama
* Llama 3.2

Install Ollama and download the model:

```bash
ollama pull llama3.2
```

Verify that the model is available:

```bash
ollama run llama3.2
```

---

## Running the Application

Clone the repository:

```bash
git clone <repository-url>
cd RAG_project
```

Build and start the containers:

```bash
docker compose up -d --build
```

The application exposes:

```text
Streamlit → http://localhost:8501
FastAPI   → http://localhost:8000
```

Open the Streamlit interface:

```text
http://localhost:8501
```

---

## Usage

### 1. Upload Documents

Use the document uploader to select one or multiple PDF files.

### 2. Build the Knowledge Base

The backend:

```text
Extracts → Chunks → Embeds → Stores
```

the uploaded documents in ChromaDB.

### 3. Ask Questions

Once indexing is complete, use the conversational interface to query the uploaded documentation.

### 4. Inspect Sources

The application displays the documents associated with the retrieved information.

### 5. Provide Feedback

Use the feedback controls to indicate whether the generated answer was useful.

---

## Design Decisions

### Why use embeddings?

Traditional keyword search can fail when the wording of the question differs significantly from the wording used in the documentation.

Embeddings provide a semantic representation that allows the system to retrieve conceptually related text even when exact keywords do not match.

### Why use a vector database?

Embedding every document chunk once and storing the resulting vectors avoids repeatedly processing the complete document collection for every query.

At query time, only the user question needs to be embedded before performing similarity search.

### Why use a separate embedding model and LLM?

The two models solve different problems:

```text
Embedding Model
      ↓
Semantic representation
      ↓
Information retrieval


LLM
      ↓
Context + Question
      ↓
Natural-language generation
```

Separating these responsibilities makes the architecture modular and allows the retrieval and generation components to be optimized independently.

### Why local inference?

Using Ollama and Llama 3.2 allows the system to perform inference locally without requiring a hosted LLM API.

This is useful for experimenting with RAG systems in privacy-sensitive scenarios and provides greater control over the inference environment.

---

## Current Limitations

The current implementation is intentionally focused on a simple, understandable RAG architecture.

Known limitations include:

* Chunking is currently based on fixed character length rather than document structure or semantic boundaries.
* Retrieval currently uses a fixed `top_k = 3`.
* No reranking stage is currently implemented.
* The evaluation dataset is still relatively small and should be expanded for more robust benchmarking.
* The current session model replaces the previous document collection rather than providing persistent multi-user workspaces.
* OCR is not implemented for scanned/image-only PDFs.
* Authentication and authorization are outside the current scope.
* Production-grade monitoring and distributed deployment are not currently implemented.

These limitations also provide clear directions for future experimentation and optimization.

---

## Future Improvements

Planned improvements include:

### Retrieval

* Experiment with different chunk sizes and overlap strategies.
* Implement structure-aware or semantic chunking.
* Compare dense retrieval with hybrid keyword + semantic retrieval.
* Add a reranking stage.
* Experiment with different embedding models.
* Tune the number of retrieved chunks.

### Evaluation

Expand the evaluation dataset and systematically compare configurations using:

* Faithfulness
* Answer Relevancy
* Context Precision
* Context Recall

A future benchmark could compare:

```text
Baseline RAG
     vs
Improved Chunking
     vs
Hybrid Retrieval
     vs
Retrieval + Reranking
```

### Engineering

* Add automated tests.
* Add structured application logging.
* Add health checks and improved error handling.
* Add authentication and user-specific workspaces.
* Improve observability and latency monitoring.
* Add CI/CD.

---

## Project Goals

This project was built to explore the engineering challenges involved in developing an end-to-end RAG system rather than simply integrating an LLM API.

The main objectives are:

* Understand the complete RAG architecture.
* Implement semantic retrieval from first principles.
* Work with embeddings and vector databases.
* Deploy a local LLM.
* Separate frontend and backend responsibilities.
* Containerize the application.
* Track document provenance.
* Establish a foundation for quantitative RAG evaluation and experimentation.

---

## License

This project is intended for educational and portfolio purposes.
