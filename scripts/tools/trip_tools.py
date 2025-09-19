import sqlite3
from typing import Optional
from pathlib import Path
import os

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from sqlalchemy.engine import row


# @tool
def search_trip_recommendations(
        location : Optional[str] = None,
        name : Optional[str] = None,
        keywords : Optional[str] = None,
        db="../../data/travel.sqlite"
) -> list[dict]:
    """
    Search for trip recommendations based on location, name, and keywords.

    Args:
        location (Optional[str]): The location of the trip recommendation. Defaults to None.
        name (Optional[str]): The name of the trip recommendation. Defaults to None.
        keywords (Optional[str]): The keywords associated with the trip recommendation. Defaults to None.

    Returns:
        list[dict]: A list of trip recommendation dictionaries matching the search criteria.
    """
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    query = "SELECT * FROM trip_recommendations WHERE 1 = 1"
    params = []

    if location:
        query += "AND location LIKE ?"
        params.append(f"%{location}%")
    if name:
        query += "AND name LIKE ?"
        params.append(f"%{name}%")
    if keywords:
        keyword_list = keywords.split(",")
        keyword_conditions = " OR ".join(["keywords LIKE ?" for _ in keyword_list])
        query += f"AND ({keyword_conditions})"
        params.extend([f"%{keyword.strip()}%" for keyword in keyword_list])

    cursor.execute(query, params)
    rows = cursor.fetchall()
    column_names = [column[0] for column in cursor.description]
    results = [dict(zip(column_names, row)) for row in rows]

    cursor.close()
    conn.close()

    return results




