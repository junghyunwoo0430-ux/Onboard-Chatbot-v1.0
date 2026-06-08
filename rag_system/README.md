# RAG 챗봇 - 백엔드

LangChain과 FastAPI를 사용하여 구축된 Retrieval-Augmented Generation (RAG) 챗봇의 백엔드 API 서버입니다. 로컬 LLM 모델(LM Studio)과 연동하여 질문에 대한 답변을 생성합니다.

## 주요 기능

- FastAPI 기반의 비동기 API 서버
- FAISS를 이용한 로컬 벡터 저장소
- LangChain을 활용한 RAG 파이프라인
- LM Studio와 같이 OpenAI API와 호환되는 로컬 LLM 연동 지원

## 사전 준비 사항

- Python 3.8 이상
- LM Studio (또는 다른 로컬 LLM 구동 프로그램)
- LM Studio에 `a.x-4.0-light`와 같은 한국어 LLM 모델이 로드되고, API 서버가 실행된 상태

## 설치 및 실행 방법

1. **`.env` 파일 설정**

   `.env.example` 파일을 복사하여 `.env` 파일을 생성합니다. 파일 안에 있는 `LLM_BASE_URL`을 자신의 로컬 LLM API 주소로 설정합니다.

2. **필요한 라이브러리 설치**

   프로젝트 폴더로 들어와 아래 명령어를 실행합니다.
   ```bash
   pip install -r requirements.txt
   ```

3. **벡터 데이터베이스 생성 (최초 1회)**

   상위 폴더에 `gknu_chatbot_data_cleaned.csv` 파일이 있는지 확인한 후, 아래 명령어를 실행하여 지식 베이스를 생성합니다.
   ```bash
   python create_vector_store.py
   ```
   `faiss_index`라는 폴더가 생성됩니다.

4. **백엔드 서버 실행**

   LM Studio의 API 서버가 켜져 있는지 확인한 후, 아래 명령어로 FastAPI 서버를 실행합니다.
   ```bash
   uvicorn app:app --host 0.0.0.0 --port 8000
   ```
   서버가 정상적으로 실행되면 `Application startup complete.` 메시지가 출력됩니다.

## API 정보

- **Endpoint**: `POST /chat`
- **Request Body**:
  ```json
  {
    "question": "여기에 질문을 입력하세요"
  }
  ```
- **Success Response**:
  ```json
  {
    "answer": "챗봇의 답변 내용입니다."
  }
  ```
