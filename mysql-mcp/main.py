import os
import mysql.connector
from fastmcp import FastMCP

# CHANGE THE VALUES ACCORDING TO YOUR CREDENTIALS
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "YourUserName")
DB_PASSWORD = os.getenv("DB_PASSWORD", "YourDBPassword")
DB_NAME = os.getenv("DB_NAME", "YourDBNmae")

# Create the MCP server
mcp = FastMCP("MySQL MCP Server")

def get_db_connection():
    """Returns a new MySQL connection."""
    return mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

@mcp.tool()
def list_tables() -> list[str]:
    """
    Return a list of all tables in the configured database.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES;")
        rows = cursor.fetchall()
        # Each row is a tuple like (tablename,)
        return [r[0] for r in rows]
    finally:
        conn.close()

@mcp.tool()
def get_table_rows(table_name: str, limit: int = 10) -> list[dict]:
    """
    Return the first `limit` rows of the specified table.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        # Prevent SQL injection: use identifier safely
        if not table_name.isidentifier():
            raise ValueError("Invalid table name")
        sql = f"SELECT * FROM `{table_name}` LIMIT %s;"
        cursor.execute(sql, (limit,))
        rows = cursor.fetchall()
        return rows
    finally:
        conn.close()

@mcp.tool()
def execute_select_query(query: str) -> list[dict]:
    """
    Execute a custom SQL SELECT query and return the results.
    Only SELECT queries are allowed for safety.
    """
    # Basic safety check - only allow SELECT queries
    query_upper = query.strip().upper()
    if not query_upper.startswith("SELECT"):
        raise ValueError("Only SELECT queries are allowed")
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        rows = cursor.fetchall()
        return rows
    finally:
        conn.close()

if __name__ == "__main__":
    mcp.run()