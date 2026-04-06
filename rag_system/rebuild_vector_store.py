from chunk_data import chunk_data
from chunk_pdf import chunk_pdf_data
from create_vector_store import create_vector_store


def main() -> None:
    chunk_data()
    chunk_pdf_data()
    create_vector_store()


if __name__ == "__main__":
    main()
