from langchain_core.tools import tool

from vector_store.vector_store import load_vector_store_as_retriever


@tool
def lookup_policy(query: str) -> str:
    """Consult the company policies to check whether certain options are permitted.
        Use this before making any flight changes performing other 'write' events."""

    retriever = load_vector_store_as_retriever()
    docs = retriever.invoke(query)
    return "\n\n".join(doc["page_content"] for doc in docs)