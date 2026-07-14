"""
db.py — Database Connection Layer
Provides helper functions for connecting to the remote TiDB Cloud MySQL database
and executing queries safely using pymysql.
"""
try:
    import pymysql
except ModuleNotFoundError:
    import sys, subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pymysql"])
finally:
    import pymysql
import os
import streamlit as st
try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    import sys, subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-dotenv"])
finally:
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


@st.cache_data(ttl=15)
def fetch_one(query, params=None):
    """Fetch a single row as a dict. Returns None if no row found."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()
    finally:
        conn.close()


@st.cache_data(ttl=15)
def fetch_all(query, params=None):
    """Fetch all rows as a list of dicts."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
    finally:
        conn.close()
