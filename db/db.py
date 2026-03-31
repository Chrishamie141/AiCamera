import sqlite3
from pathlib import Path

DB_PATH = Path("backend/db/events.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    with open("backend/db/schema.sql", "r") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
