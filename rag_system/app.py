import os
from typing import List

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_openai import ChatOpenAI

from config import (
    get_api_prefix,
    get_context_max_chars,
    get_cors_origins,
    get_embedding_model,
    get_faiss_path,
    get_llm_base_url,
    get_openai_api_key,
    get_retriever_k,
)


def format_docs(docs: List[Document], max_chars: int | None = None) -> str:
    limit = max_chars or get_context_max_chars()
    parts = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source") or doc.metadata.get("path") or ""
        parts.append(f"[{i}] (src: {source})\n{doc.page_content.strip()}\n")

    text = "\n---\n".join(parts).strip()
    return text[:limit] if len(text) > limit else text


def setup_rag_chain():
    faiss_path = get_faiss_path()
    if not faiss_path.exists():
        raise FileNotFoundError(
            f"Vector store not found at '{faiss_path}'. Run create_vector_store.py first."
        )

    embeddings = HuggingFaceEmbeddings(model_name=get_embedding_model())
    vectorstore = FAISS.load_local(str(faiss_path), embeddings, allow_dangerous_deserialization=True)
    retriever = vectorstore.as_retriever(search_kwargs={"k": get_retriever_k()})

    template = """
당신은 Webonomics 회사 정보를 안내하는 AI 챗봇입니다.
아래 가이드라인을 따라 답변을 생성해 주세요.

[가이드라인]
1) 검색된 정보가 질문과 관련이 있다면 해당 정보를 우선 사용합니다.
2) 검색된 정보만으로 부족하면 일반 지식을 보완해 답변합니다.
3) 답변은 항상 친절하고 명확한 한국어로 작성합니다.

[검색된 정보]
{context}

[질문]
{question}

[답변]
""".strip()

    prompt = ChatPromptTemplate.from_template(template)
    llm = ChatOpenAI(
        base_url=get_llm_base_url(),
        api_key=get_openai_api_key(),
    )

    return (
        {
            "context": retriever | RunnableLambda(format_docs),
            "question": RunnablePassthrough(),
        }
        | prompt
        | llm
        | StrOutputParser()
    )


api_prefix = get_api_prefix()

app = FastAPI(
    title="Webonomics RAG Chatbot",
    docs_url=f"{api_prefix}/docs",
    openapi_url=f"{api_prefix}/openapi.json",
)
cors_origins = get_cors_origins()
api_router = APIRouter(prefix=api_prefix)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=cors_origins != ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    question: str


rag_chain = None


@app.on_event("startup")
def on_startup():
    global rag_chain
    print("Loading RAG chain...")
    rag_chain = setup_rag_chain()
    print("RAG chain loaded.")


def build_service_info():
    return {
        "service": "Webonomics RAG Chatbot",
        "status": "ok" if rag_chain is not None else "initing",
        "docs": f"{api_prefix}/docs",
        "openapi": f"{api_prefix}/openapi.json",
        "chat_endpoints": ["/chat", f"{api_prefix}/chat"],
        "health_endpoints": ["/health", f"{api_prefix}/health"],
    }


@app.get("/")
def root():
    return build_service_info()


@app.get(api_prefix)
def version_root():
    return build_service_info()


@app.get("/health")
def health():
    return {"status": "ok" if rag_chain is not None else "initing"}


@api_router.get("/health")
def versioned_health():
    return health()


def handle_chat(request: ChatRequest):
    if rag_chain is None:
        return JSONResponse(status_code=500, content={"answer": "챗봇이 아직 초기화되지 않았습니다."})

    question = (request.question or "").strip()
    if not question:
        return JSONResponse(status_code=400, content={"answer": "질문을 입력해 주세요."})

    try:
        answer = (rag_chain.invoke(question) or "").strip()
        return {"answer": answer}
    except Exception as exc:
        print(f"[ERROR] Chat request failed: {exc!r}")
        return JSONResponse(
            status_code=500,
            content={"answer": "질문을 처리하는 중 서버 오류가 발생했습니다."},
        )


@app.post("/chat")
def chat(request: ChatRequest):
    return handle_chat(request)


@api_router.post("/chat")
def versioned_chat(request: ChatRequest):
    return handle_chat(request)


app.include_router(api_router)


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("BACKEND_PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
