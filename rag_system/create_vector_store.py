import json

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.docstore.document import Document
from langchain_community.vectorstores import FAISS

from config import get_data_paths, get_embedding_model, get_faiss_path


def create_vector_store() -> None:
    print("Loading chunked data...")
    records = []

    data_paths = get_data_paths()
    faiss_path = get_faiss_path()
    embedding_model = get_embedding_model()

    for data_path in data_paths:
        print(f"Reading from {data_path}...")
        try:
            if not data_path.exists():
                print(f"Warning: data file '{data_path}' was not found.")
                continue

            with data_path.open("r", encoding="utf-8") as file:
                for line in file:
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    content = record.get("content", "").strip()
                    metadata = record.get("metadata", {})
                    if content:
                        records.append(Document(page_content=content, metadata=metadata))
        except Exception as exc:
            print(f"Failed to read '{data_path}': {exc}")

    if not records:
        print("No valid documents were loaded. Vector store creation skipped.")
        return

    print(f"Loaded {len(records)} documents.")
    print(f"Loading embedding model '{embedding_model}'...")
    embeddings = HuggingFaceEmbeddings(model_name=embedding_model)
    print("Embedding model loaded.")

    try:
        faiss_path.parent.mkdir(parents=True, exist_ok=True)
        vectorstore = FAISS.from_documents(records, embeddings)
        vectorstore.save_local(str(faiss_path))
        print(f"Vector store saved to '{faiss_path}'.")
    except Exception as exc:
        print(f"Failed to create vector store: {exc}")


if __name__ == "__main__":
    create_vector_store()
