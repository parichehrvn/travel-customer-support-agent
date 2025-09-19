from dotenv import load_dotenv
from datetime import datetime
import os

from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableConfig

from state import State
from travel_agent.tools.policy_tools import lookup_policy
from travel_agent.tools.trip_tools import (
    search_trip_recommendations,
    book_excursion,
    update_excursion,
    cancel_excursion
)
from travel_agent.tools.flight_tools import (
    fetch_user_flight_information,
    search_flights,
    update_ticket_to_new_flight,
    cancel_ticket,
)


load_dotenv()
API_KEY = os.getenv("MISTRAL_API_KEY")


class Assistant:
    def __init__(self, runnable: Runnable):
        self.runnable = runnable

    def __call__(self, state: State, config: RunnableConfig):
        while True:
            configuration = config.get("configurable", {})
            passenger_id = configuration.get("passenger_id", None)
            state = {**state, "user_info": passenger_id}
            result = self.runnable.invoke(state)

            # If the LLM happens to return an empty response, we will re-prompt it for an actual response.
            if not result.tool_calls and (
                not result.content
                or isinstance(result.content, list)
                and not result.content[0].get("text")
            ):
                messages = state["messages"] + [("user", "Respond with a real output.")]
                state = {**state, "messages": messages}
            else:
                break
        return {"messages": result}


def build_assistant() -> Assistant:
    """Factory function to create an Assistant with prompt, LLM, and tools."""
    llm = ChatOpenAI(
        model="mistralai/mistral-7b-instruct:free",
        temperature=1,
        api_key=API_KEY,
        base_url="https://openrouter.ai/api/v1"
    )

    primary_assistant_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a helpful customer support assistant for Swiss Airlines. "
                " Use the provided tools to search for flights, company policies, and other information to assist the user's queries. "
                " When searching, be persistent. Expand your query bounds if the first search returns no results. "
                " If a search comes up empty, expand your search before giving up."
                "\n\nCurrent user:\n<User>\n{user_info}\n</User>"
                "\nCurrent time: {time}.",
            ),
            ("placeholder", "{messages}"),
        ]
    ).partial(time=datetime.now)

    part_1_tools = [
        TavilySearchResults(max_results=1),
        fetch_user_flight_information,
        search_flights,
        lookup_policy,
        update_ticket_to_new_flight,
        cancel_ticket,
        search_trip_recommendations,
        book_excursion,
        update_excursion,
        cancel_excursion,
    ]

    runnable = primary_assistant_prompt | llm.bind_tools(part_1_tools)
    return Assistant(runnable)
