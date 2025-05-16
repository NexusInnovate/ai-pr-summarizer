import sqlite3
import uuid
from typing import Optional, Tuple

def connect_db(db_name: str):
    try:
        print(f"Connecting to the database {db_name}...")
        return sqlite3.connect(db_name)
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        raise

def create_table(db_name: str, table_name: str):
    try:
        print(f"Started creating table...")
        with connect_db(db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS {table_name} (
                    pr_id TEXT PRIMARY KEY,
                    summary TEXT
                )
            ''')
            conn.commit()
            print(f"Table '{table_name}' exists or was created successfully.")
    except sqlite3.Error as e:
        print(f"SQLite error while creating table '{table_name}': {e}")
        raise

def fetch_pr_details_by_id(db_name: str, table_name: str, pr_id: str) -> Optional[Tuple]:
    try:
        print(f"Fetching details for PR {pr_id}...")
        with connect_db(db_name) as conn:
            cursor = conn.cursor()
            query = f"SELECT pr_id, summary FROM {table_name} WHERE pr_id = ?"
            cursor.execute(query, (pr_id,))
            row = cursor.fetchone()
            print(f"Fecthed the details successfully for : {pr_id}")
            return row
    except sqlite3.OperationalError as e:
        if "no such table" in str(e):
            create_table(db_name, table_name)
            return None
        else:
            print(f"Error during fetch: {e}")
            raise

def insert_pr_details(db_name: str, table_name: str, pr_id: str, summary: str) -> Tuple:
    try:
        with connect_db(db_name) as conn:
            cursor = conn.cursor()
            query = f"INSERT INTO {table_name} (pr_id, summary) VALUES (?, ?)"
            cursor.execute(query, (pr_id, summary))
            conn.commit()
    except sqlite3.Error as e:
        print(f"Error inserting PR details: {e}")
        raise