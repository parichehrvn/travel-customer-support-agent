import logging

from travel_agent.core.graph_builder import build_basic_graph
from travel_agent.core.helpers import _print_event
from scripts.setup_db import update_dates

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

graph = build_basic_graph()

db = 'data/travel.sqlite'
db = update_dates(db)


def run_rag(passenger_id: str, thread_id: str, question: str):
    """
    Run the RAG pipeline with memory support and return the streamed answer.

    Args:
        passenger_id (str): Passenger ID.
        thread_id (str): Identifier for the conversation thread to maintain memory.
        question (str): The user's question.

    Returns:
        Iterator[str]: Streamed response from the LLM.
    """

    try:
        config = {
            "configurable": {
                # The passenger_id is used in our flight tools to
                # fetch the user's flight information
                "passenger_id": passenger_id,
                # Checkpoints are accessed by thread_id
                "thread_id": thread_id,
            }
        }

        for message_chunk, metadata in graph.stream(
                {"messages": [{"role": "user", "content": question}]},
                stream_mode="messages",
                config=config,
        ):
            if message_chunk.content and metadata["langgraph_node"] != "tools":
                yield message_chunk.content

    except Exception as e:
        logger.error("Error running RAG pipeline: %s", e)
        return iter([f"[Error running RAG pipeline: {e}]"])