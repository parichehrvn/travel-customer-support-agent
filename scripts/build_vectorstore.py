import os
import re
from pathlib import Path
from uuid import uuid4

import requests

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain.schema import Document
import faiss


def download_faq(url):
    response = requests.get(url)
    response.raise_for_status()
    faq_text = response.text

    # Split FAQ into chunks by Markdown section
    docs = [Document(page_content=text) for text in re.split(r"(?=\n##)", faq_text)]

    return docs


def main():
    url = "https://storage.googleapis.com/benchmarks-artifacts/travel-db/swiss_faq.md"
    docs = download_faq(url)

    uuids = [str(uuid4()) for _ in range(len(docs))]

    # Initialize Hugging Face embeddings
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    dim = len(embeddings.embed_query("hello world"))

    # Create HNSW index
    index = faiss.IndexHNSWFlat(dim, 32)  # M=32 neighbors
    index.hnsw.efConstruction = 40
    index.hnsw.efSearch = 16

    # Create FAISS vector store
    vector_store = FAISS(
        embedding_function=embeddings,
        index=index,
        docstore=InMemoryDocstore(),
        index_to_docstore_id={},
    )

    vector_store.add_documents(documents=docs, ids=uuids)

    # Persist FAISS index
    storage_dir = Path(__file__).parent.parent / "storage"
    storage_dir.mkdir(parents=True, exist_ok=True)
    vector_store.save_local(str(storage_dir))


if __name__ == "__main__":
    main()