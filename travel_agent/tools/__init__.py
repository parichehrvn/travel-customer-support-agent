import os

from .policy_tools import lookup_policy
from .trip_tools import (
    search_trip_recommendations,
    book_excursion,
    update_excursion,
    cancel_excursion
)
from .flight_tools import (
    fetch_user_flight_information,
    search_flights,
    update_ticket_to_new_flight,
    cancel_ticket,
)

from langchain_community.tools.tavily_search import TavilySearchResults

from dotenv import load_dotenv
load_dotenv()
tavily_api_key = os.getenv("TAVILY_API_KEY")

tools = [
    TavilySearchResults(max_results=1, tavily_api_key=tavily_api_key),
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