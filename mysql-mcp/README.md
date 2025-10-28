## 🛠 Prerequisites

Before running this MCP, make sure you have the following installed:

- **Python 3.10+**  
  Check with:
  ```bash
  python --version
  ```
- **MySQL Server (Local or remote)**
- **Python packages**
  Use:
  ```bash
  pip install fastmcp mysql-connector-python
  ```
- **An AI client (Claude, ChatGPT Pro, etc.)**

## ⚙️ Setup Instructions

- **Set your own environment variable values (You can edit the main.py variables directly)**
- **Set the path towards your Python script**
  Example with claude_desktop_config.json file:
  ```json
  {
    "mcpServers": {
    "my-server": {
      "command": "C:\\path\\to\\python.exe",
      "args": ["C:\\path\\to\\main.py"]
    }
  }
  }
  ```
- **Enable MCP tools on your AI client**
- **Query your database using your AI** 