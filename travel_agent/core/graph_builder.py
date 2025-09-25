from typing import Any

from langgraph.graph.state import CompiledStateGraph

from travel_agent.core.helpers import create_tool_node_with_fallback
from travel_agent.core.agent import build_assistant
from travel_agent.core.state import State
from travel_agent.tools import fetch_user_flight_information, tools

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, StateGraph, START
from langgraph.prebuilt import tools_condition


def user_info(state: State):
    return {"user_info": fetch_user_flight_information.invoke({})}


def build_basic_graph():
    """Builds the customer support assistant graph for flights, trips, and policies."""

    assistant = build_assistant()
    builder = StateGraph(State)

    # Define nodes
    builder.add_node("fetch_user_info", user_info)
    builder.add_node("assistant", assistant)
    builder.add_node("tools", create_tool_node_with_fallback(tools))

    # Define edges: these determine how the control flow moves
    builder.add_edge(START, "fetch_user_info")
    builder.add_edge("fetch_user_info", "assistant")
    builder.add_conditional_edges(
        "assistant",
        tools_condition,
    )
    builder.add_edge("tools", "assistant")

    memory = InMemorySaver()

    # The graph will always halt before executing the "tools" node.
    # The user can approve or reject (or even alter the request) before
    # the assistant continues
    graph = builder.compile(
        checkpointer=memory,
        interrupt_before=["tools"]
    )

    return graph