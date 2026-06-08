# Webonomics 챗봇 세팅 가이드

이 문서는 처음 맡는 사람도 바로 따라 할 수 있도록 만든 운영/설치 문서입니다.  
목표는 아래 3가지입니다.

1. 프로그램을 새 PC 또는 새 서버에 쉽게 설치하기
2. 새로운 데이터가 생겼을 때 쉽게 추가하기
3. 내부 시스템에서 API로 쉽게 연동하기

---

## 1. 이 프로그램이 하는 일

이 프로그램은 `이주배경 학생의 교육권 및 대학 입시 정보 접근` 관련 자료를 기반으로 답변하는 챗봇입니다.

구성은 아래처럼 되어 있습니다.

- 프론트엔드: 사용자 채팅 화면
- 백엔드: 질문 처리, 문서 검색, LLM 호출
- 지식 DB: FAISS 벡터 DB
- 데이터 원본:
  - 웹사이트 크롤링 데이터
  - `newData` 폴더에 넣은 PDF 파일

동작 순서는 아래와 같습니다.

1. 웹사이트와 PDF에서 텍스트를 모읍니다.
2. 긴 텍스트를 작은 단위로 자릅니다.
3. 잘린 텍스트를 벡터 DB로 만듭니다.
4. 사용자가 질문하면 관련 문서를 찾습니다.
5. LLM이 찾은 자료를 참고해서 답변합니다.

---

## 2. 폴더 설명

- `rag_frontend`
  - 사용자 화면
- `rag_system`
  - 백엔드 API
  - 벡터 DB 생성 스크립트
- `gknu_crawler`
  - 웹 데이터 수집 코드
- `newData`
  - 새 PDF 자료를 넣는 곳
- `webonomics_chunked.jsonl`
  - 웹 문서 청킹 결과
- `pdf_chunked.jsonl`
  - PDF 청킹 결과
- `rag_system/faiss_index`
  - 실제 검색용 벡터 DB

---

## 3. 가장 쉬운 실행 방법: Docker

개별 운영할 때는 Docker 방식이 가장 편합니다.

### 3-1. 준비물

- Docker Desktop 또는 Docker Engine
- Docker Compose
- LLM 서버 주소
  - 예: LM Studio
  - 예: 사내 OpenAI 호환 API 서버

### 3-2. 최초 1회 설정

프로젝트 루트에서 아래를 실행합니다.

```bash
copy .env.docker.example .env
```

그 다음 `.env` 파일에서 아래 값만 먼저 확인하면 됩니다.

- `LLM_BASE_URL`
  - 같은 PC에서 LM Studio 사용 시:
    - `http://host.docker.internal:1234/v1`
  - 다른 서버에 LLM이 있을 때:
    - `http://서버IP:포트/v1`

- `API_BASE_URL`
  - 기본값 그대로 사용 권장: `/api/v1`

- `API_PREFIX`
  - 기본값 그대로 사용 권장: `/v1`

### 3-3. 실행

```bash
docker compose up --build -d
```

### 3-4. 접속 주소

- 프론트엔드: `http://localhost:8080`
- 백엔드 상태 확인: `http://localhost:8000/v1/health`
- 백엔드 API 문서: `http://localhost:8000/v1/docs`

---

## 4. Docker 없이 직접 실행하는 방법

개발 또는 긴급 점검 시만 권장합니다.

### 4-1. 백엔드 실행

```bash
cd rag_system
copy .env.example .env
pip install -r requirements.txt
python create_vector_store.py
uvicorn app:app --host 0.0.0.0 --port 8000
```

### 4-2. 프론트엔드 실행

```bash
cd rag_frontend
npm install
npm start
```

브라우저 접속:

- `http://localhost:3000`

---

## 5. 운영자가 꼭 알아야 하는 핵심 파일

- 환경설정 예시: [rag_system/.env.example](C:/Users/user/Desktop/newC/rag_system/.env.example)
- 도커 환경설정 예시: [.env.docker.example](C:/Users/user/Desktop/newC/.env.docker.example)
- 도커 실행 파일: [docker-compose.yml](C:/Users/user/Desktop/newC/docker-compose.yml)
- 백엔드 API: [rag_system/app.py](C:/Users/user/Desktop/newC/rag_system/app.py)
- 벡터 DB 재생성: [rag_system/rebuild_vector_store.py](C:/Users/user/Desktop/newC/rag_system/rebuild_vector_store.py)

---

## 6. 새로운 데이터가 생기면 어떻게 추가하나

이 부분이 가장 중요합니다.  
운영자가 해야 할 일은 크게 2가지입니다.

1. 새 자료를 넣기
2. 벡터 DB 다시 만들기

### 6-1. PDF 자료 추가

새 PDF 파일을 아래 폴더에 넣습니다.

- [newData](C:/Users/user/Desktop/newC/newData)

예시:

- 인사규정 PDF
- 취업규칙 PDF
- 회사 소개서 PDF
- 매뉴얼 PDF

### 6-2. 웹사이트 데이터가 바뀐 경우

웹사이트 내용을 다시 수집해야 하면 크롤러를 다시 실행합니다.

현재 주요 수집 결과 파일은 아래입니다.

- [gknu_crawler/webonomics_all_pages.jsonl](C:/Users/user/Desktop/newC/gknu_crawler/webonomics_all_pages.jsonl)

필요하면 크롤링 로직은 아래를 수정합니다.

- [gknu_crawler/crawler.py](C:/Users/user/Desktop/newC/gknu_crawler/crawler.py)

### 6-3. 가장 쉬운 갱신 방법

새 데이터 추가 후 아래 명령 한 줄이면 됩니다.

```bash
cd rag_system
python rebuild_vector_store.py
```

이 명령은 아래 3개를 순서대로 실행합니다.

1. 웹 문서 청킹
2. PDF 청킹
3. FAISS 벡터 DB 재생성

### 6-4. Docker 운영 중일 때

```bash
docker compose exec backend python rebuild_vector_store.py
docker compose restart backend
```

### 6-5. 데이터 추가 체크리스트

아래 순서로 하면 실수가 적습니다.

1. 새 PDF를 `newData` 폴더에 넣는다
2. 웹 자료가 바뀌었으면 크롤링 결과도 갱신한다
3. `rebuild_vector_store.py`를 실행한다
4. 백엔드를 재시작한다
5. 대표 질문 3~5개로 테스트한다

---

## 7. API를 쉽게 쓰는 방법

회사 시스템 연동용으로 API는 버전형 엔드포인트를 기본으로 맞춰두었습니다.

권장 기본 주소:

- 상태 확인: `GET /v1/health`
- 채팅 질문: `POST /v1/chat`
- API 문서: `GET /v1/docs`
- OpenAPI 스펙: `GET /v1/openapi.json`

기존 호환용 경로도 남겨두었습니다.

- `GET /health`
- `POST /chat`

### 7-1. 왜 `/v1`을 쓰는가

내부에서 오래 운영하면 API가 바뀔 수 있습니다.  
처음부터 `/v1` 형태로 쓰면 나중에 `/v2`를 추가해도 기존 연동을 덜 깨뜨릴 수 있습니다.

### 7-2. 가장 쉬운 호출 예시

```bash
curl -X POST http://localhost:8000/v1/chat ^
  -H "Content-Type: application/json" ^
  -d "{\"question\":\"회사 인사 규정 요약해줘\"}"
```

응답 예시:

```json
{
  "answer": "..."
}
```

### 7-3. 사내 시스템에서 권장하는 방식

사내 다른 서비스에서는 아래처럼 쓰는 것을 권장합니다.

1. 프론트 서비스 연동 시
   - `http://서버주소:8080`

2. 백엔드 직접 연동 시
   - `http://서버주소:8000/v1/chat`

3. API 명세 확인 시
   - `http://서버주소:8000/v1/docs`

### 7-4. 프론트에서 API 주소를 바꾸는 방법

프론트엔드는 API 주소를 코드에 고정하지 않고 설정값으로 받습니다.

관련 파일:

- [rag_frontend/public/config.js](C:/Users/user/Desktop/newC/rag_frontend/public/config.js)
- [rag_frontend/public/config.template.js](C:/Users/user/Desktop/newC/rag_frontend/public/config.template.js)

기본값은 아래처럼 맞춰져 있습니다.

- 로컬 직접 호출: `http://localhost:8000/v1`
- Docker/Nginx 경유: `/api/v1`

즉, 서버 주소가 바뀌어도 프론트 코드를 크게 고치지 않아도 됩니다.

---

## 8. 새 서버로 옮길 때 순서

### 8-1. 가장 쉬운 이관 절차

1. 새 서버에 Docker 설치
2. 프로젝트 전체 폴더 복사
3. `.env` 파일 수정
4. LLM 서버 연결 확인
5. 아래 실행

```bash
docker compose up --build -d
```

6. 아래 주소 확인

- `http://서버주소:8000/v1/health`
- `http://서버주소:8000/v1/docs`
- `http://서버주소:8080`

### 8-2. 이관 후 꼭 확인할 것

1. LLM 서버가 실제로 응답하는지
2. PDF가 제대로 읽혔는지
3. 벡터 DB가 생성됐는지
4. 대표 질문 답변이 정상인지
5. 방화벽/포트가 열려 있는지

---

## 9. 자주 쓰는 명령어 모음

### 전체 실행

```bash
docker compose up --build -d
```

### 중지

```bash
docker compose down
```

### 로그 보기

```bash
docker compose logs -f backend
docker compose logs -f frontend
```

### 벡터 DB 다시 만들기

```bash
docker compose exec backend python rebuild_vector_store.py
```

### 백엔드 재시작

```bash
docker compose restart backend
```

---

## 10. 문제 생겼을 때 먼저 볼 것

### 챗봇 답변이 안 나올 때

확인 순서:

1. `http://localhost:8000/v1/health` 접속
2. LLM 서버 주소 확인
3. 벡터 DB 존재 여부 확인
4. Docker 로그 확인

### 새 PDF를 넣었는데 반영이 안 될 때

확인 순서:

1. `newData` 폴더에 파일이 들어갔는지
2. `rebuild_vector_store.py`를 다시 돌렸는지
3. 백엔드를 재시작했는지

### API 주소가 헷갈릴 때

운영 기준으로는 아래만 기억하면 됩니다.

- 사용자 화면: `8080`
- 백엔드 API: `8000/v1`
- API 문서: `8000/v1/docs`

---

## 11. 추천 운영 원칙

실무에서는 아래처럼 운영하는 것을 추천합니다.

1. 운영 API는 항상 `/v1`로 사용
2. 새 데이터 추가 후에는 대표 질문으로 검증
3. PDF 원본은 별도 백업
4. `.env` 값은 서버별로 분리 관리
5. 배포 전에는 API 문서(`/v1/docs`)로 테스트

---

## 12. 한 줄 요약

가장 쉬운 운영 방법은 아래입니다.

1. 자료는 `newData`에 넣는다
2. `docker compose exec backend python rebuild_vector_store.py` 실행
3. 필요하면 `docker compose restart backend`
4. 사용자는 `8080`, 연동 시스템은 `8000/v1/chat` 사용
