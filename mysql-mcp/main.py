import os
import mysql.connector
from fastmcp import FastMCP

# CHANGE THE VALUES ACCORDING TO YOUR CREDENTIALS
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "YourUserName")
DB_PASSWORD = os.getenv("DB_PASSWORD", "YourDBPassword")
DB_NAME = os.getenv("DB_NAME", "YourDBName")

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

@mcp.tool()
def count_rows(table_name: str) -> dict:
    """
    Return the total number of rows in a table.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`;")
        count = cursor.fetchone()[0]
        return {"table": table_name, "row_count": count}
    finally:
        conn.close()

@mcp.tool()
def search_table(table_name: str, keyword: str, limit: int = 10) -> list[dict]:
    """
    Search for a keyword across all text-like columns in a given table.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)

        cursor.execute(f"SHOW COLUMNS FROM `{table_name}`;")
        columns = [c["Field"] for c in cursor.fetchall() if "char" in c["Type"] or "text" in c["Type"]]

        if not columns:
            return [{"info": "No searchable text columns found."}]

        like_conditions = " OR ".join([f"`{col}` LIKE %s" for col in columns])
        params = tuple([f"%{keyword}%"] * len(columns))

        sql = f"SELECT * FROM `{table_name}` WHERE {like_conditions} LIMIT %s;"
        cursor.execute(sql, (*params, limit))
        return cursor.fetchall()
    finally:
        conn.close()

@mcp.tool()
def get_table_schema(table_name: str) -> list[dict]:
    """
    Return the schema (columns, types, keys) for a given table.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(f"DESCRIBE `{table_name}`;")
        return cursor.fetchall()
    finally:
        conn.close()

@mcp.tool()
def get_foreign_keys(table_name: str) -> list[dict]:
    """
    Return all foreign key relationships for a given table.
    Shows which columns reference other tables.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT 
                COLUMN_NAME AS column_name,
                REFERENCED_TABLE_NAME AS referenced_table,
                REFERENCED_COLUMN_NAME AS referenced_column
            FROM information_schema.KEY_COLUMN_USAGE
            WHERE 
                TABLE_SCHEMA = %s
                AND TABLE_NAME = %s
                AND REFERENCED_TABLE_NAME IS NOT NULL;
        """
        cursor.execute(query, (DB_NAME, table_name))
        rows = cursor.fetchall()
        if not rows:
            return [{"info": f"No foreign keys found for table '{table_name}'."}]
        return rows
    finally:
        conn.close()

if __name__ == "__main__":
    mcp.run()