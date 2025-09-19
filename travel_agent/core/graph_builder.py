from helpers import create_tool_node_with_fallback
from agent import build_assistant
from state import State
from travel_agent.tools import tools

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, StateGraph, START
from langgraph.prebuilt import tools_condition


def build_basic_graph() -> StateGraph:
    """Builds the customer support assistant graph for flights, trips, and policies."""

    assistant = build_assistant()
    builder = StateGraph(State)

    # Define nodes
    builder.add_node("assistant", assistant)
    builder.add_node("tools", create_tool_node_with_fallback(tools))

    # Define edges: these determine how the control flow moves
    builder.add_edge(START, "assistant")
    # builder.add_conditional_edges(
    #
    # )