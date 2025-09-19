import sqlite3
from datetime import date, datetime
from typing import Optional

import pytz
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from sympy.matrices.benchmarks.bench_matrix import timeit_Matrix_zeronm

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


@tool
def update_ticket_to_new_flight(
    ticket_no: str, new_flight_id: int, *, config: RunnableConfig, db="../data/travel.sqlite"
) -> str:
    """Update the user's ticket to a new valid flight."""
    try:
        configuration = config["configurable"]
        passenger_id = configuration["passenger_id"]

        conn = sqlite3.connect(db)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT departure_airport, arrival_airport, scheduled_departure FROM flights WHERE flight_id = ?",
            (new_flight_id,),
        )

        new_flight = cursor.fetchone()
        if not new_flight:
            cursor.close()
            conn.close()
            return "Invalid new flight ID provided."

        column_names = [column[0] for column in cursor.description]
        new_flight_dict = dict(zip(column_names, new_flight))
        timezone = pytz.timezone("Etc/GMT-3")
        current_time = datetime.now(tz=timezone)
        departure_time = datetime.strptime(
            new_flight_dict["scheduled_departure"], "%Y-%m-%d %H:%M:%S.%f%z"
        )
        time_until = (departure_time - current_time).total_seconds()
        if time_until < (3 * 3600):
            return f"Not permitted to reschedule to a flight that is less than 3 hours from the current time. Selected flight is at {departure_time}."

        cursor.execute(
            "SELECT flight_id FROM ticket_flights WHERE ticket_no = ?",
            (ticket_no,)
        )
        current_flight = cursor.fetchone()
        if not current_flight:
            cursor.close()
            conn.close()
            return "No existing ticket found for the given ticket number."

        # Check the signed-in user actually has this ticket
        cursor.execute(
            "SELECT * FROM tickets WHERE ticket-no = ? AND passenger_id = ?",
            (ticket_no, passenger_id)
        )
        current_ticket = cursor.fetchone()
        if not current_ticket:
            cursor.close()
            conn.close()
            return f"Current signed-in passenger with ID {passenger_id} not the owner of ticket {ticket_no}"

        cursor.execute(
            "UPDATE ticket_flights SET flight_id = ? WHERE ticket_no = ?",
            (new_flight_id, ticket_no)
        )
        conn.commit()

        cursor.close()
        conn.close()
        return "Ticket successfully updated to new flight."

    except KeyError as e:
        print(e)



