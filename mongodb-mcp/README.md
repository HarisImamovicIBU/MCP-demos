# 🍃 MongoDB MCP Server

A lightweight **MongoDB Read-Only MCP (Model Context Protocol) server** that allows your AI client to:

- List all collections  
- Inspect collection schemas  
- Execute safe `find` queries  
- Run secure aggregation pipelines  
- Fetch sample documents  

All operations are strictly **read-only** for maximum safety.

## 🛠 Prerequisites

Before running this MCP server, make sure you have:

- **Python 3.10+**
  ```bash
  python --version
  ```
- **MongoDB (local or remote)**
- **Required Python packages**
  ```bash
  pip install fastmcp pymongo bson
  ```
- **An MCP-enabled AI client** (ChatGPT Desktop, Claude Desktop, etc.)

## ⚙️ Setup Instructions

### 1️⃣ Configure Environment Variables (optional)

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_HOST` | MongoDB host | `localhost` |
| `DB_PORT` | MongoDB port | `27017` |
| `DB_USER` | Username | *(empty)* |
| `DB_PASSWORD` | Password | *(empty)* |
| `DB_NAME` | Database name | `sample_restaurants` |
| `MAX_QUERY_TIME` | Aggregation timeout (ms) | `30000` |
| `MAX_ROWS` | Max returned rows | `10000` |
| `ENABLE_QUERY_LOGGING` | Print logs | `true` |

(You may also edit these directly in `main.py`.)

### 2️⃣ Register the MCP Server

Example `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "mongo-mcp": {
      "command": "C:\\path\\to\\python.exe",
      "args": ["C:\\path\\to\\main.py"]
    }
  }
}
```

### 3️⃣ Enable MCP Tools

Enable the MCP integration inside your AI client so it can detect the server.

### 4️⃣ Query MongoDB Using Natural Language

Ask things like:

- “List all collections.”
- “Show the schema for the \`restaurants\` collection.”
- “Find Italian restaurants, limit 5.”
- “Aggregate restaurants by borough.”

## 🔒 Safety

This server enforces **read-only** access.

❌ No inserts  
❌ No updates  
❌ No deletes  
❌ No `$out` or `$merge`  

Allowed:

✅ `find`  
✅ `aggregate` (read-only stages only)  
✅ `count`  
✅ Schema sampling  
✅ Collection statistics  

Your AI client will automatically detect and use the MCP server, if you configured everything correctly.
