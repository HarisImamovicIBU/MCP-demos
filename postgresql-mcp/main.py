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
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "11235813"),
    "database": os.getenv("DB_NAME", "ClassicModels")
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

# AI-executables
@mcp.tool()
def execute_select_query(query: str) -> List[Dict[str, Any]]:
    """
    Execute a custom SQL SELECT query with security validation.
    
    Args:
        query: SQL SELECT query to execute
        
    Security:
        - Only SELECT, SHOW, EXPLAIN, WITH queries allowed
        - Dangerous operations blocked
        - Query timeout protection
        - Row limit enforcement
    """
    start_time = time.time()
    
    try:
        is_valid, error_msg = validate_query_safety(query)
        if not is_valid:
            raise ValueError(f"Security validation failed: {error_msg}")
        
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(f"SET statement_timeout = {MAX_QUERY_TIME * 1000}")
            cursor.execute(query)
            rows = cursor.fetchall()
            
            if len(rows) > MAX_ROWS:
                raise ValueError(f"Query returned {len(rows)} rows, exceeding limit of {MAX_ROWS}")
            
            duration = time.time() - start_time
            log_info(f"Query executed in {duration:.3f}s, returned {len(rows)} rows")
            
            return [dict(row) for row in rows]
    except Exception as e:
        log_error(f"Query execution error: {e}")
        raise

@mcp.tool()
def count_rows(table_name: str, schema_name: str = "classicmodels") -> Dict[str, Any]:
    """
    Return the total number of rows in a table.
    
    Args:
        table_name: Name of the table
        schema_name: Schema name (default: classicmodels)
    """
    try:
        table_name = sanitize_identifier(table_name)
        schema_name = sanitize_identifier(schema_name)
        
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(f'SELECT COUNT(*) as count FROM "{schema_name}"."{table_name}"')
            result = cursor.fetchone()
            return {
                "table": f"{schema_name}.{table_name}",
                "row_count": result["count"]
            }
    except Exception as e:
        log_error(f"count_rows error: {e}")
        raise

if __name__ == "__main__":
    init_pool()
    mcp.run()