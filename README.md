**Project Title**
## RAG Agentic System with FastAPI, LangChain & Chroma

## Table of Contents
1. Description

2. Features

3. Prerequisites

4. Installation

5. Configuration

6. Data Pipeline

7. Agent Server (FastAPI)

8. Usage

9. Project Structure

10. License

**Description**
This project implements a Retrieval-Augmented Generation (RAG) agent using:

LangChain for orchestration and tool calling

Chroma vector store for document embeddings and similarity search

Sentence-Transformer embeddings (all-MiniLM-L6-v2) for semantic search

FastAPI to expose a streaming chat UI via Server-Sent Events (SSE) and a JSON API

It ingests daily Federal Register documents into a vector DB and serves them via an agent that can answer user queries in real time. 


## Features
Automated ingestion of regulatory documents from the Federal Register

Chunking and embedding of text for efficient semantic search

Agentic reasoning with tool calls (RAG) and memory support

FastAPI UI with live streaming chat (SSE)

Modular codebase for easy extension

## Prerequisites
Python 3.10


## Installation

```bash
# Clone the repository
git clone https://github.com/JisnaP/Rag_Agent_for_Streaming_Data.git

cd Rag_Agent_for_Streaming_Data

# Create and activate a virtual environment
conda create -p ./venv python=3.10 -y
conda activate ./venv

# Install dependencies
pip install -r requirements.txt

```

##  Configuration


```dotenv
OPENAI_KEY=your_openai_api_key

```
## Data Pipeline


The data_pipeline.py script:

1. Fetches documents from https://www.federalregister.gov/api/v1/documents.json

2. Processes and splits them into 1 000-character chunks

3. Embeds with SentenceTransformerEmbeddings

4. Persists into a Chroma DB at ./chroma_db

To ingest streaming data run with:

```python 
python scheduler.py
```

After successful ingestion you should see logs like:


```cpp
Length of all_splits :248
Ingestion complete and vector store persisted.
```

## Agent Server (FastAPI)


The app.py exposes:

**GET / **: HTML chat UI

**GET /api/query?message=… **: SSE endpoint for streaming agent replies

**POST /api/json_query **: return full answer as JSON


```python
uvicorn app:app --host 127.0.0.1 --port 8000
````

Open your browser at http://127.0.0.1:8000/.

## Project Structure 

```csharp 
├── agent.py           # LangGraph agent setup
├── app.py             # FastAPI server
├── data_pipeline.py   # Ingestion & embedding
├── chroma_db/         # Persisted vector store
├── templates/
│   └── index.html     # Chat UI
├── static/
│   └── app.js         # Front-end logic
├── requirements.txt   # Python dependencies
└── README.md          # README file
```

## Lisence 
MIT Lisence