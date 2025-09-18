import os
import shutil
import sqlite3

import pandas as pd
import requests


def download_dataset(db_url, local_file, backup_file):
    if not os.path.exists(local_file):
        response = requests.get(db_url)
        response.raise_for_status()
        with open(local_file, "wb") as f:
            f.write(response.content)
        shutil.copy(local_file, backup_file)


def update_dates(db_file):
    # establish a connection to an SQLite database
    conn = sqlite3.connect(db_file)

    # get tables names
    tables = pd.read_sql(
            "SELECT name FROM sqlite_master WHERE type='table';", conn
    ).name.tolist()

    tdf = {}
    for t in tables:
        tdf[t] = pd.read_sql(f"SELECT * from {t}", conn)

    # latest actual departure time in the flights table (acts as the reference point for time adjustment)
    example_time = pd.to_datetime(
        tdf["flights"]["actual_departure"].replace("\\N", pd.NaT)
    ).max()
    current_time = pd.to_datetime("now").tz_localize(example_time.tz)
    time_diff = current_time - example_time

    # update dates
    tdf["bookings"]["book_date"] = (
        pd.to_datetime(tdf["bookings"]["book_date"].replace("\\N", pd.NaT), utc=True)
        + time_diff
    )

    datetime_columns = [
        "scheduled_departure",
        "scheduled_arrival",
        "actual_departure",
        "actual_arrival",
    ]
    for column in datetime_columns:
        tdf["flights"][column] = (
            pd.to_datetime(tdf["flights"][column].replace("\\N", pd.NaT)) + time_diff
        )

    # save updated tables
    for table_name, df in tdf.items():
        df.to_sql(table_name, conn, if_exists="replace", index=False)

    del df
    del tdf
    conn.commit()
    conn.close()

    return db_file


def main():
    db_url = "https://storage.googleapis.com/benchmarks-artifacts/travel-db/travel2.sqlite"
    local_file = "../data/travel.sqlite"
    backup_file = "../data/travel.backup.sqlite"

    download_dataset(db_url, local_file, backup_file)
    db = update_dates(local_file)
    return db


if __name__ == "__main__":
    main()