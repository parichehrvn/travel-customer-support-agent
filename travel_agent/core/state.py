from typing import Annotated

import langgraph.graph.message
from typing_extensions import TypedDict

from langgraph.graph.message import AnyMessage, add_messages


class State(TypedDict):
    """“
    messages is a list of chat messages, and whenever the state is updated, new messages should be added to the list
    """
    messages: Annotated[list[AnyMessage], add_messages]
    user_info: str