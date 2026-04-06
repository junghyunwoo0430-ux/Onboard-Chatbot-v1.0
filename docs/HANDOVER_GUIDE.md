# Webonomics Chatbot Handover Guide

## 1. Program Summary

This project is a RAG-based chatbot system for Webonomics company data.

- Frontend: React chat UI
- Backend: FastAPI + LangChain
- Knowledge base: FAISS vector store
- Data sources:
  - crawled website content
  - PDF files placed in `newData`
- LLM: OpenAI-compatible API such as LM Studio

## 2. Folder Summary

- `rag_frontend`: React frontend
- `rag_system`: FastAPI backend and vector store build scripts
- `gknu_crawler`: website crawling code
- `newData`: PDF files to include in the knowledge base
- `webonomics_chunked.jsonl`: chunked website data
- `pdf_chunked.jsonl`: chunked PDF data
- `rag_system/faiss_index`: generated vector database

## 3. How the System Works

1. Website pages are collected by the crawler.
2. Crawled content and PDF files are chunked into text blocks.
3. Chunk data is embedded with `jhgan/ko-sroberta-multitask`.
4. FAISS stores the embeddings as a vector database.
5. FastAPI retrieves related chunks and sends the prompt to the LLM.
6. React displays the answer to the user.

## 4. Local Run

### Backend

```bash
cd rag_system
pip install -r requirements.txt
copy .env.example .env
python create_vector_store.py
uvicorn app:app --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd rag_frontend
npm install
npm start
```

Frontend default URL: `http://localhost:3000`

## 5. Docker Run

1. Prepare environment values.

```bash
copy .env.docker.example .env
```

2. Set `LLM_BASE_URL` in `.env`
   - LM Studio on the same PC: `http://host.docker.internal:1234/v1`
   - External LLM server: `http://<SERVER_IP>:<PORT>/v1`

3. Start services.

```bash
docker compose up --build -d
```

4. Access services.
   - Frontend: `http://localhost:8080`
   - Backend health: `http://localhost:8000/v1/health`
   - API docs: `http://localhost:8000/v1/docs`

## 6. Rebuild the Knowledge Base

### Full rebuild

```bash
cd rag_system
python rebuild_vector_store.py
```

This runs:

1. `chunk_data.py`
2. `chunk_pdf.py`
3. `create_vector_store.py`

### Separate steps

```bash
cd rag_system
python chunk_data.py
python chunk_pdf.py
python create_vector_store.py
```

## 7. How to Add a New Target DB

1. Put new PDF files in `newData`
2. If website data changed, run or update the crawler
3. Rebuild chunk files and FAISS index
4. Restart backend

For Docker:

```bash
docker compose exec backend python rebuild_vector_store.py
docker compose restart backend
```

## 8. Server Migration Checklist

1. Install Docker and Docker Compose
2. Copy the project folder to the new server
3. Copy `.env` or `.env.docker` settings
4. Confirm the LLM API is reachable from the new server
5. Run `docker compose up --build -d`
6. Check `http://<server>:8000/health`
7. Open the frontend and test a few representative questions

## 9. Delivery Items

- Program source code
- Docker deployment files
- Installation and operation guide
- Method for rebuilding a new knowledge base
