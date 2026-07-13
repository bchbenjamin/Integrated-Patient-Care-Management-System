"""
db.py — Database Connection Layer
Provides helper functions for connecting to the remote TiDB Cloud MySQL database
and executing queries safely using pymysql.
"""

import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    """Returns a pymysql connection to the TiDB Cloud database."""
    return pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 4000)),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "ipcms"),
        ssl={"ssl": True} if os.getenv("DB_HOST", "localhost") != "localhost" else None,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )


def execute_query(query, params=None):
    """Execute an INSERT/UPDATE/DELETE query. Returns lastrowid for INSERTs."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.lastrowid
    finally:
        conn.close()


def fetch_one(query, params=None):
    """Fetch a single row as a dict. Returns None if no row found."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()
    finally:
        conn.close()


def fetch_all(query, params=None):
    """Fetch all rows as a list of dicts."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
    finally:
        conn.close()
