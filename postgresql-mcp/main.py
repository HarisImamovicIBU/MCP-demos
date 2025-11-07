import os
import sys
import re
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from contextlib import contextmanager
import psycopg2
from psycopg2 import pool, Error
from psycopg2.extras import RealDictCursor
from fastmcp import FastMCP

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "user": int(os.getenv("DB_USER", "YourUsername")),
    "password": os.getenv("DB_PASSWORD", "YourPassword"),
    "database": os.getenv("DB_NAME", "classicmodels")
}

# Safety variables
MAX_QUERY_TIME = int(os.getenv("MAX_QUERY_TIME", 30))
MAX_ROWS = int(os.getenv("MAX_ROWS", 10000))
ENABLE_QUERY_LOGGING = os.getenv("ENABLE_QUERY_LOGGING", "true").lower()=="true"
CONNECTION_POOL = None
NOT_ALLOWED_PATTERNS = [
    r'\bDROP\b', r'\bDELETE\b', r'\bTRUNCATE\b', r'\bINSERT\b',
    r'\bUPDATE\b', r'\bALTER\b', r'\bCREATE\b', r'\bGRANT\b',
    r'\bREVOKE\b', r'\bCOPY\b', r'\bEXECUTE\b'
] # Read-only for now

#MCP initialization
mcp = FastMCP(
    name="PostgreSQL MCP",
    stateless_http=True,
    instructions="""
    This MCP server provides read-only access to the Classicmodels PostgreSQL database.

    Available capabilities:
    - List all tables and views in the database
    - View table schema and relationships
    - Execute SELECT queries safely

    Security: Only SELECT, SHOW and EXPLAIN queries are allowed.
    All write operations are blocked for safety.
    """
)

# Utils
def init_pool():
    """Initialize connection pool"""
    global CONNECTION_POOL
    try:
        CONNECTION_POOL = psycopg2.pool.SimpleConnectionPool(
            minconn=1,
            maxconn=int(os.getenv("DB_POOL_SIZE", 5)),
            **DB_CONFIG
        )
        log_info("Database connection pool initialized successfully!")
    except Error as e:
        log_error(f"Failed to initialize connection pool: {e}")
        sys.exit(1)

@contextmanager
def get_db_connection():
    """Context manager for database connections with auto-cleanup"""
    connection = None
    try:
        connection = CONNECTION_POOL.getconn()
        yield connection
    except Exception as e:
        log_error(f"Database connection error: {e}")
        raise Exception(str(e))
    finally:
        if connection:
            CONNECTION_POOL.putconn(connection)

def log_info(message: str):
    """Log informational messages to stderr"""
    if ENABLE_QUERY_LOGGING:
        timestamp = datetime.now().isoformat()
        print(f"[{timestamp}] INFO: {message}", file=sys.stderr)

def log_error(message: str):
    """Log error messages to stderr"""
    timestamp = datetime.now().isoformat()
    print(f"[{timestamp}] ERROR: {message}", file=sys.stderr)

# Safety functions
def validate_query_safety(query: str) -> tuple[bool, Optional[str]]:
    """
    Validate that query is safe to execute.
    Returns (is_valid, error_message)
    """
    query_upper = query.strip().upper()
    
    allowed_starts = ["SELECT", "SHOW", "EXPLAIN", "WITH", "TABLE"]
    if not any(query_upper.startswith(cmd) for cmd in allowed_starts):
        return False, "Only SELECT, SHOW, EXPLAIN, and WITH queries are allowed"
    
    for pattern in NOT_ALLOWED_PATTERNS:
        if re.search(pattern, query_upper):
            return False, f"Query contains forbidden operation"
    
    # Check for multiple statements
    if ';' in query.rstrip(';'):
        return False, "Multiple statements are not allowed"
    
    return True, None

def sanitize_identifier(identifier: str) -> str:
    """Sanitize table/column names to prevent SQL injection"""
    if not re.match(r'^[a-zA-Z0-9_\.]+$', identifier):
        raise ValueError(f"Invalid identifier: {identifier}")
    return identifier