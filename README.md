# Onboard Chatbot (온보드 챗봇) 프로젝트

## 1. 프로젝트 개요

Python FastAPI로 구현된 백엔드가 LangChain을 사용하여 지식 베이스에서 관련 정보를 검색하고, LM Studio를 통해 구동되는 로컬 LLM이 최종 답변을 생성합니다. React로 제작된 프론트엔드는 사용자가 편리하게 챗봇과 상호작용할 수 있는 웹 인터페이스를 제공합니다.

<img width="1125" height="1336" alt="image" src="https://github.com/user-attachments/assets/ca4a6ada-c4ba-43be-bae3-9773486b9c91" />


## 2. 기술 스택

- **백엔드**: Python, FastAPI, LangChain, FAISS, Sentence-Transformers
- **프론트엔드**: React, Bootstrap, Axios, React-Markdown
- **LLM 환경**: LM Studio (또는 OpenAI 호환 API를 제공하는 로컬 서버)

## 3. 프로젝트 구조

```
.
├── chatbot_data_cleaned.csv  # RAG를 위한 정제된 데이터
├── rag_frontend/                  # React 프론트엔드
│   ├── public/
│   ├── src/
│   └── README.md                  # (프론트엔드 상세 안내)
└── rag_system/                    # Python 백엔드
    ├── faiss_index/               # (생성됨) 벡터 데이터베이스
    ├── app.py
    ├── create_vector_store.py
    └── README.md                  # (백엔드 상세 안내)
```

## 4. 시스템 실행 방법 (Quick Start)

전체 시스템을 실행하기 위해서는 백엔드 서버와 프론트엔드 서버를 각각 구동해야 합니다.

### 1단계: 백엔드 서버 실행

자세한 내용은 `rag_system/README.md` 파일을 참고하세요.

1.  **LM Studio 실행**: 사용하고자 하는 LLM 모델을 로드하고 API 서버를 시작합니다.
2.  **`.env` 파일 생성**: `rag_system` 폴더의 `.env.example` 파일을 복사하여 `.env` 파일을 만들고, 필요시 `LLM_BASE_URL`을 자신의 환경에 맞게 수정합니다.
3.  **터미널 1**: `rag_system` 폴더로 이동하여 아래 명령어로 백엔드 서버를 실행합니다.
    ```bash
    # 종속성 설치 (최초 1회)
    pip install -r requirements.txt

    # 벡터 DB 생성 (최초 1회)
    python create_vector_store.py

    # 서버 실행
    uvicorn app:app --host 0.0.0.0 --port 8000
    ```

### 2단계: 프론트엔드 서버 실행

자세한 내용은 `rag_frontend/README.md` 파일을 참고하세요.

1.  **터미널 2**: `rag_frontend` 폴더로 이동하여 아래 명령어로 프론트엔드 개발 서버를 실행합니다.
    ```bash
    # 종속성 설치 (최초 1회)
    npm install

    # 서버 실행
    npm start
    ```
2.  **접속**: 웹 브라우저에서 `http://localhost:3000` 주소로 접속하여 챗봇을 사용합니다.
"# Onboard-Chatbot-v1.0" 
