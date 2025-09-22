
import pandas as pd
from langchain_community.document_loaders import DataFrameLoader
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
import os

# 벡터 저장소와 데이터 파일 경로 설정
FAISS_PATH = "faiss_index"
DATA_PATH = "../gknu_chatbot_data_cleaned.csv" # 상위 폴더의 CSV 파일

def create_vector_store():
    """
    데이터를 로드하고, 임베딩을 생성하여 FAISS 벡터 저장소를 만듭니다.
    """
    # 데이터 로딩
    print("데이터를 로드하는 중...")
    try:
        df = pd.read_csv(DATA_PATH)
        # 'text' 열에 결측치가 있는 행 제거
        df.dropna(subset=['text'], inplace=True)
        
        if df.empty:
            print("오류: CSV 파일을 로드했으나 유효한 데이터가 없습니다. 'text' 열을 확인해주세요.")
            return

        loader = DataFrameLoader(df, page_content_column="text")
        documents = loader.load()
        print(f"{len(documents)}개의 문서를 로드했습니다.")

    except FileNotFoundError:
        print(f"오류: 데이터 파일 '{DATA_PATH}'을(를) 찾을 수 없습니다.")
        print("스크립트가 'rag_system' 폴더 내에서 실행되고 있는지, 상위 폴더에 'gknu_chatbot_data_cleaned.csv' 파일이 있는지 확인해주세요.")
        return
    except Exception as e:
        print(f"데이터 로딩 중 오류 발생: {e}")
        return

    # 임베딩 모델 설정
    print("임베딩 모델을 로드하는 중... (시간이 걸릴 수 있습니다)")
    # 한국어 자연어 처리에 특화된 모델 사용
    model_name = "jhgan/ko-sroberta-multitask" 
    embeddings = HuggingFaceEmbeddings(model_name=model_name)
    print("임베딩 모델 로드 완료.")

    # FAISS 벡터 저장소 생성 및 저장
    print("FAISS 벡터 저장소를 생성하는 중...")
    try:
        vectorstore = FAISS.from_documents(documents, embeddings)
        vectorstore.save_local(FAISS_PATH)
        print(f"벡터 저장소가 '{FAISS_PATH}' 폴더에 성공적으로 저장되었습니다.")
    except Exception as e:
        print(f"벡터 저장소 생성 중 오류 발생: {e}")


if __name__ == "__main__":
    create_vector_store()
