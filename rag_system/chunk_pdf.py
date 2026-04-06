import glob
import json
import os
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import PROJECT_ROOT

INPUT_DIR = PROJECT_ROOT / "newData"
OUTPUT_PATH = PROJECT_ROOT / "pdf_chunked.jsonl"


def chunk_pdf_data(input_dir: Path = INPUT_DIR, output_path: Path = OUTPUT_PATH) -> None:
    if not input_dir.exists():
        print(f"Error: Directory {input_dir} not found.")
        return

    pdf_files = glob.glob(os.path.join(str(input_dir), "*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in {input_dir}.")
        return

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
    )

    chunked_records = []
    print(f"Found {len(pdf_files)} PDF files in {input_dir}...")

    for pdf_path in pdf_files:
        print(f"Processing {pdf_path}...")
        try:
            loader = PyPDFLoader(pdf_path)
            chunks = loader.load_and_split(text_splitter)

            for index, chunk in enumerate(chunks):
                content = chunk.page_content.strip()
                if not content:
                    continue

                metadata = dict(chunk.metadata)
                metadata["chunk"] = index
                chunked_records.append(
                    json.dumps(
                        {
                            "content": content,
                            "metadata": metadata,
                        },
                        ensure_ascii=False,
                    )
                )
        except Exception as exc:
            print(f"Error processing {pdf_path}: {exc}")

    print(f"Writing {len(chunked_records)} chunks to {output_path}...")
    with output_path.open("w", encoding="utf-8") as file:
        for record in chunked_records:
            file.write(record + "\n")

    print("PDF Chunking complete.")


if __name__ == "__main__":
    chunk_pdf_data()
