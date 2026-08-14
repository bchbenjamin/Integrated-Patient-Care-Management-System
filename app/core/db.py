import pymysql
import os
from dotenv import load_dotenv
from dbutils.pooled_db import PooledDB
from cachetools import TTLCache

load_dotenv()

# Initialize connection pool
# pool of 5 connections, max 20
pool = PooledDB(
    creator=pymysql,
    maxconnections=20,
    mincached=5,
    maxcached=20,
    blocking=True,
    host=os.getenv('DB_HOST', 'localhost'),
    port=int(os.getenv('DB_PORT', 4000)),
    user=os.getenv('DB_USER', 'root'),
    password=os.getenv('DB_PASSWORD', ''),
    database=os.getenv('DB_NAME', 'ipcms'),
    ssl={'ssl': True} if os.getenv('DB_HOST', 'localhost') != 'localhost' else None,
    cursorclass=pymysql.cursors.DictCursor,
    autocommit=True,
)

# Initialize query cache (SELECT query results for 60 seconds)
query_cache = TTLCache(maxsize=1024, ttl=60)

def cache_bust():
    """Clear the query cache."""
    query_cache.clear()

def _make_cache_key(query, params):
    if params is None:
        return query
    if isinstance(params, (list, tuple)):
        return (query, tuple(params))
    if isinstance(params, dict):
        return (query, frozenset(params.items()))
    return (query, str(params))

def get_connection():
    return pool.connection()

def execute_query(query, params=None):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            result = cursor.lastrowid
        
        # Call cache_bust after mutations
        upper_query = query.strip().upper()
        if upper_query.startswith(("INSERT", "UPDATE", "DELETE", "REPLACE", "DROP", "CREATE", "ALTER")):
            cache_bust()
            
        return result
    finally:
        conn.close()

def fetch_one(query, params=None):
    is_select = query.strip().upper().startswith("SELECT")
    if is_select:
        cache_key = _make_cache_key(query, params)
        if cache_key in query_cache:
            return query_cache[cache_key]

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            result = cursor.fetchone()
            
            if is_select:
                query_cache[cache_key] = result
                
            return result
    finally:
        conn.close()

def fetch_all(query, params=None):
    is_select = query.strip().upper().startswith("SELECT")
    if is_select:
        cache_key = _make_cache_key(query, params)
        if cache_key in query_cache:
            return query_cache[cache_key]

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            result = cursor.fetchall()
            
            if is_select:
                query_cache[cache_key] = result
                
            return result
    finally:
        conn.close()
