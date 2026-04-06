import json
import re
import logging
import time # crawl_date에 사용하기 위해 import
from typing import List, Dict

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataCleaner:
    def __init__(self, input_knowledge_file: str, output_knowledge_file: str, output_chunks_file: str):
        self.input_knowledge_file = input_knowledge_file
        self.output_knowledge_file = output_knowledge_file
        self.output_chunks_file = output_chunks_file
        self.cleaned_documents: List[Dict] = []
        self.rag_chunks: List[Dict] = []

        # 웹사이트의 고정적인 메뉴/푸터 텍스트 패턴 (정규식)
        # 이 패턴들은 실제 웹사이트 구조를 기반으로 더 정교하게 조정될 수 있습니다.
        self.boilerplate_patterns = [
            r"회사소개 회사소개 회사연혁 회사현황 조직과 인력 인재채용 오시는길 사업분야 웹 솔루션 개발 홈페이지 제작 쇼핑몰 제작 모바일 웹/앱 제작 온라인 마케팅 클라우드 사업실적 지자체 전자상거래 솔루션 제작 온도모니터링 솔루션 개발 학교 급식관리 및 Haccp 운영 솔루션 개발 DID 및 메뉴보드 솔루션 개발 홈페이지 제작 구축문의 구축문의 고객센터 일반유지보수 클라우드 고객센터 주메뉴로 바로가기 본문으로 바로가기 회사소개 회사소개 회사연혁 회사현황 조직과 인력 인재채용 오시는길 사업분야 웹 솔루션 개발 홈페이지 제작 쇼핑몰 제작 모바일 웹/앱 제작 온라인 마케팅 클라우드 사업실적 지자체 전자상거래 솔루션 제작 온도모니터링 솔루션 개발 학교 급식관리 및 Haccp 운영 솔루션 개발 DID 및 메뉴보드 솔루션 개발 홈페이지 제작 구축문의 구축문의 고객센터 일반유지보수 클라우드 고객센터 홈 회원가입 로그인 공지사항 웨보노믹스 고객의 성공을 생각하는 자가 고객을 성공하게 만듭니다. \(주\)웨보노믹스",
            r"회사소개 오시는길 이용약관 개인정보처리방침 채용안내 공식블로그 상호 : \(주\)웨보노믹스 대표 : 김용군 대표전화 : 1644-4548 이메일 : webon@hanmail.net Fax : 054-841-5377 본사 : \(우:36759\) 경북 안동시 풍천면 천년숲서로 7-19 화인비즈니스타운 2층 201호 사업자등록번호 : 508-81-08034 서울지점 : \(우:06762\) 서울 서초구 바우뫼로7길 8, B2 개인정보관리책임자 : 장미숙 상단으로",
            r"주메뉴로 바로가기 본문으로 바로가기",
            r"홈 회원가입 로그인 공지사항",
            r"웨보노믹스 고객의 성공을 생각하는 자가 고객을 성공하게 만듭니다. \(주\)웨보노믹스",
            r"웹어플리케이션, 데이터분석, 모니터링, 전자상거래, 모바일", # 공통 description 텍스트
            r"회사소개 오시는길 이용약관 개인정보처리방침 채용안내 공식블로그", # 푸터 상단 링크
            r"상단으로", # 페이지 상단 이동 링크 텍스트
            r"글쓰기 처음 이전 \d+ 페이지 \d+ 페이지 다음 맨끝", # 게시판 페이징
            r"현재 \d+ 개 업체의 고객님이 유지관리 서비스를 이용중에 있습니다.", # 유지보수 페이지 상단 문구
            r"인터넷 접수 는 전화나 메일 접수보다 우선 처리됩니다\. \(인터넷 > 메일 > 팩스 > 전화 > 방문접수 순\) 접수된 다음날부터 접수순으로 처리되며, 처리에서 완료까지 \d+~?\d*일 정도소요 \(근무일기준\)됩니다\. 당일 또는 즉시처리를 원하시는 경우 유지보수 서비스에 상관없이 추가비용이 발생 됩니다\. 호스팅전용고객은 반드시 작업비가 청구되며, 서비스고객이라도 작업량에 따라 비용을 청구 할 수 있습니다\. 추가 작업비는 선 결제 를 원칙으로 하며, \d+개월 이상 미납요금이 있을시 유지보수 처리가 되지 않습니다\. 요청하시는 내용을 가능한 상세히 기록해 주세요\. \*\^\^\* 정확한 수정확인을 위해서 쿠키삭제를 꼭! 해주세요\. ※ 웹하드 안내 ID : webon P/W : webon4548 \[바로가기\] 파일을 올리실때\? GUEST폴더 > 올리기전용 폴더 안에 업로드해주세요\. 크롬 및 엣지 정책에 의해 SSL 보안인증서 미설치 시 크롬 및 엣지에서 안전하지 않는 사이트 안내 및 카드결제가 진행되지 않을수 있습니다\. 보안인증설치는 유상으로 진행되는 관계로 유지보수 신청을 통해 설치가 가능합니다\. ※SSL란\(웹사이트 이용자와 송수신시 정보를 암호화하여 안전하게 주고 받는 보안구축방법\)", # 유지보수 페이지 설명
            r"[(주)웨보노믹스]" # title에 (주)웨보노믹스가 포함되는 경우 중복 제거
        ]

    def load_documents(self, file_path: str) -> List[Dict]:
        """지정된 JSON 파일에서 문서를 로드합니다."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get('documents', [])
        except FileNotFoundError:
            logger.error(f"Error: Input file '{file_path}' not found.")
            return []
        except json.JSONDecodeError:
            logger.error(f"Error: Could not decode JSON from '{file_path}'. Check file format.")
            return []

    def clean_text_content(self, text: str) -> str:
        """텍스트에서 상용구 패턴을 제거합니다."""
        for pattern in self.boilerplate_patterns:
            text = re.sub(pattern, '', text).strip()
        text = re.sub(r'\s+', ' ', text).strip() # 여러 공백을 단일 공백으로
        return text

    def filter_and_clean(self):
        """문서를 필터링하고 콘텐츠를 정리합니다."""
        documents = self.load_documents(self.input_knowledge_file)
        logger.info(f"Loaded {len(documents)} documents from '{self.input_knowledge_file}'.")

        for doc in documents:
            title = doc.get('title', '')
            content = doc.get('content', '')
            url = doc.get('url', '')

            # 1. '비밀번호 입력' 페이지 제외
            if "비밀번호 입력" in title:
                logger.debug(f"  제외: 비밀번호 입력 페이지 - {url}")
                continue
            
            # 2. 상용구 텍스트 제거
            cleaned_content = self.clean_text_content(content)
            
            # 3. 정리 후 너무 짧은 콘텐츠 제외
            if len(cleaned_content) < 50:
                logger.debug(f"  제외: 정리 후 너무 짧은 콘텐츠 ({len(cleaned_content)} 글자) - {url}")
                continue

            # 정리된 문서 추가
            self.cleaned_documents.append({
                'url': url,
                'title': title,
                'description': doc.get('description', ''), # description은 그대로 유지
                'content': cleaned_content,
                'length': len(cleaned_content)
            })
        
        logger.info(f"Finished cleaning. {len(self.cleaned_documents)} documents remaining.")

    def save_cleaned_documents(self):
        """정리된 문서를 새 JSON 파일로 저장합니다."""
        output_data = {
            "metadata": {
                "source": "webonomics.co.kr",
                "total_documents": len(self.cleaned_documents),
                "cleaned_date": time.strftime('%Y-%m-%d %H:%M:%S'), # current time
                "description": "웨보노믹스 RAG 지식 저장소 (정리됨)"
            },
            "documents": self.cleaned_documents
        }
        with open(self.output_knowledge_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        logger.info(f"Cleaned documents saved to '{self.output_knowledge_file}'.")
    
    def create_rag_chunks(
        self,
        chunk_size: int = 500,
        overlap: int = 50
    ):
        """
        RAG 시스템용 텍스트 청크 생성 (정리된 문서 기반)
        """
        if not self.cleaned_documents:
            logger.warning("No cleaned documents to create chunks from. Run filter_and_clean first.")
            return

        chunk_id = 0
        for page in self.cleaned_documents:
            # 제목 + 설명 + 본문 결합
            full_text = f"[{page['title']}]\n{page['description']}\n\n{page['content']}"

            words = full_text.split()

            step = chunk_size - overlap
            for i in range(0, len(words), step):
                chunk_words = words[i:i + chunk_size]

                if len(chunk_words) < 50: # 최소 청크 길이
                    continue

                chunk_text = ' '.join(chunk_words)

                self.rag_chunks.append({
                    'chunk_id': chunk_id,
                    'source_url': page['url'],
                    'source_title': page['title'],
                    'chunk_text': chunk_text,
                    'chunk_length': len(chunk_words)
                })
                chunk_id += 1
        logger.info(f"\n✂️  RAG 청크 생성 완료: {len(self.rag_chunks)}개")

    def save_chunks_to_json(self):
        """청크를 JSON으로 저장"""
        chunks_data = {
            'metadata': {
                'total_chunks': len(self.rag_chunks),
                'chunk_size': 500,
                'overlap': 50,
                'description': 'LLM 임베딩 및 벡터 저장소용 청크 (정리된 문서 기반)'
            },
            'chunks': self.rag_chunks
        }

        with open(self.output_chunks_file, 'w', encoding='utf-8') as f:
            json.dump(chunks_data, f, ensure_ascii=False, indent=2)

        logger.info(f"💾 청크 저장 완료: '{self.output_chunks_file}'")


def main():
    input_knowledge_file = 'webonomics_rag_knowledge.json'
    output_knowledge_file = 'webonomics_rag_knowledge_cleaned.json'
    output_chunks_file = 'webonomics_rag_chunks_cleaned.json'
    
    cleaner = DataCleaner(input_knowledge_file, output_knowledge_file, output_chunks_file)
    cleaner.filter_and_clean()
    cleaner.save_cleaned_documents()
    cleaner.create_rag_chunks()
    cleaner.save_chunks_to_json()

if __name__ == "__main__":
    main()