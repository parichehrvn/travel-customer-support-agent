import sqlite3
from datetime import date, datetime
from typing import Optional

import pytz
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig

from vector_store import load_vector_store_as_retriever


@tool
def lookup_policy(query: str) -> str:
    """Consult the company policies to check whether certain options are permitted.
        Use this before making any flight changes performing other 'write' events."""

    retriever = load_vector_store_as_retriever()
    docs = retriever.invoke(query)
    return "\n\n".join(doc["page_content"] for doc in docs)

@tool
def fetch_user_flight_information(config: RunnableConfig, db="../data/travel.sqlite") -> list[dict]:
    """Fetch all tickets for the user along with corresponding flight information and seat assignments.

    Returns:
        A list of dictionaries where each dictionary contains the ticket details,
        associated flight details, and the seat assignments for each ticket belonging to the user.
    """
    try:
        configuration = config["configurable"]
        passenger_id = configuration["passenger_id"]

        conn = sqlite3.connect(db)
        cursor = conn.cursor()

        query = """
        SELECT
            t.ticket_no, t.book_ref,
            f.flight_id, f.flight_no, f.departure_airport, f.arrival_airport, f.scheduled_departure, f.scheduled_arrival,
            bp.seat_no, tf.fare_conditions
        FROM
            tickets t
            JOIN ticket_flights tf ON t.ticket_no = t.ticket_no
            JOIN flights f ON tf.flight_id=f.flight_id
            JOIN boarding_passes bp ON bp.ticket_no=t.ticket_no AND bp.flight_id=f.flight_id
        WHERE
            t.passenger_id = ?
        """

        cursor.execute(query, (passenger_id,))
        rows = cursor.fetchall()

        column_names = [column[0] for column in cursor.description]
        results = [dict(zip(column_names, row)) for row in rows]

        cursor.close()
        conn.close()

        return results

    except KeyError as e:
        print(e)

