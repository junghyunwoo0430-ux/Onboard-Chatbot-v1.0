import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi.responses import JSONResponse

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# --- RAG 체인 설정 (기존 코드 활용) ---
FAISS_PATH = "faiss_index"
EMBEDDING_MODEL = "jhgan/ko-sroberta-multitask"

def setup_rag_chain():
    # .env 파일에서 환경 변수 로드
    load_dotenv()

    if not os.path.exists(FAISS_PATH):
        raise FileNotFoundError(f"오류: 벡터 저장소 '{FAISS_PATH}'를 찾을 수 없습니다. 'create_vector_store.py'를 먼저 실행해주세요.")

    llm_base_url = os.getenv("LLM_BASE_URL")
    if not llm_base_url:
        raise ValueError("환경 변수 'LLM_BASE_URL'이 설정되지 않았습니다. .env 파일을 확인해주세요.")

    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    vectorstore = FAISS.load_local(FAISS_PATH, embeddings, allow_dangerous_deserialization=True)
    retriever = vectorstore.as_retriever()

    template = '''
    당신은 국립경국대학교의 정보를 알려주는 친절한 AI 챗봇입니다.
    사용자의 질문에 답변하기 위해 아래의 검색된 정보를 참고하세요.
    정보에 없는 내용이라면, 상상해서 답변하지 말고 모른다고 솔직하게 말하세요.
    답변은 항상 한국어로 해주세요.

    [검색된 정보]
    {context}

    [질문]
    {question}

    [답변]
    '''
    prompt = ChatPromptTemplate.from_template(template)

    llm = ChatOpenAI(
        base_url=llm_base_url,
        api_key="not-needed"
    )

    rag_chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    return rag_chain

# --- FastAPI 애플리케이션 설정 ---
app = FastAPI()

# CORS 미들웨어 설정 (React 앱과 통신하기 위함)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 운영 시에는 React 앱의 주소로 변경하는 것이 안전합니다.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

class ChatRequest(BaseModel):
    question: str

from fastapi.responses import JSONResponse

# RAG 체인 전역 변수로 로드
rag_chain = None

@app.on_event("startup")
def on_startup():
    global rag_chain
    print("RAG 체인을 로드합니다...")
    rag_chain = setup_rag_chain()
    print("RAG 체인 로드 완료.")

@app.post("/chat")
def chat(request: ChatRequest):
    if rag_chain is None:
        return JSONResponse(status_code=500, content={"answer": "오류: 챗봇이 초기화되지 않았습니다."})
    
    try:
        question = request.question
        answer = rag_chain.invoke(question)
        return {"answer": answer}
    except Exception as e:
        print(f"Error during RAG chain invocation: {e}")
        return JSONResponse(status_code=500, content={"answer": "죄송합니다, 질문을 처리하는 동안 서버에서 오류가 발생했습니다."})

# 서버 실행을 위한 uvicorn 설정
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)