# 🐘 PostgreSQL MCP Server

A lightweight **PostgreSQL Read-Only MCP (Model Context Protocol) server** that allows your AI client to:

- List all tables and views  
- Inspect table schemas and relationships  
- Execute safe `SELECT` queries  
- Count rows in tables  

All operations are strictly **read-only** for maximum safety.

## 🛠 Prerequisites

Before running this MCP server, make sure you have:

- **Python 3.10+**
  ```bash
  python --version
  ```
- **PostgreSQL (local or remote)**
- **Required Python packages**
  ```bash
  pip install fastmcp psycopg2
  ```
- **An MCP-enabled AI client** (ChatGPT Desktop, Claude Desktop, etc.)

## ⚙️ Setup Instructions

### 1️⃣ Configure Environment Variables (optional)

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_HOST` | PostgreSQL host | `localhost` |
| `DB_PORT` | PostgreSQL port | `5432` |
| `DB_USER` | Username | `YourUsername` |
| `DB_PASSWORD` | Password | `YourPassword` |
| `DB_NAME` | Database name | `ClassicModels` |
| `MAX_QUERY_TIME` | Query timeout (seconds) | `30` |
| `MAX_ROWS` | Max rows returned | `10000` |
| `ENABLE_QUERY_LOGGING` | Print logs | `true` |
| `DB_POOL_SIZE` | Connection pool max size | `5` |

(You may also edit these directly in `main.py`.)

### 2️⃣ Register the MCP Server

Example `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "postgres-mcp": {
      "command": "C:\\path\\to\\python.exe",
      "args": ["C:\\path\\to\\main.py"]
    }
  }
}
```

### 3️⃣ Enable MCP Tools

Enable the MCP integration inside your AI client so it can detect the server.

### 4️⃣ Query PostgreSQL Using Natural Language

Ask things like:

- “List all tables in the database.”
- “Count rows in the `customers` table.”
- “Execute a SELECT query on `orders`.”

## 🔒 Safety

This server enforces **read-only** access.

❌ No INSERT, UPDATE, DELETE, TRUNCATE, ALTER, DROP, CREATE, GRANT, REVOKE, COPY, EXECUTE  
✅ Only `SELECT`, `SHOW`, `EXPLAIN`, `WITH` queries are allowed  
✅ Single-statement queries only  
✅ Query timeout and row limits enforced  

Your AI client will automatically detect and use the MCP server.
