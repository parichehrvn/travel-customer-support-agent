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


@tool
def search_flights(
    departure_airport: Optional[str] = None,
    arrival_airport: Optional[str] = None,
    start_time: Optional[date | datetime] = None,
    end_time: Optional[date | datetime] = None,
    limit: int = 20,
    db="../data/travel.sqlite"
) -> list[dict]:
    """Search for flights based on departure airport, arrival airport, and departure time range."""
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    query = "SELECT * FROM flights WHERE 1 = 1"
    params = []

    if departure_airport:
        query += "AND departure_airport = ?"
        params.append(departure_airport)

    if arrival_airport:
        query += " AND arrival_airport = ?"
        params.append(arrival_airport)

    if start_time:
        query += " AND scheduled_departure >= ?"
        params.append(start_time)

    if end_time:
        query += " AND scheduled_departure <= ?"
        params.append(end_time)

    query += "LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    column_names = [column[0] for column in cursor.description]
    results = [dict(zip(column_names, row)) for row in rows]

    cursor.close()
    conn.close()

    return results


