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
            r""
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
