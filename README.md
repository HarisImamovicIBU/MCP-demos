# MCP-demos
Welcome to **MCP-demos** — a collection of **mini MCP (Model Context Protocol) projects** demonstrating how to connect AI models with different databases.  

This repository showcases how to build lightweight MCP servers that expose database resources for AI or developer consumption.

---

## 🚀 Project Overview

MCPs allow you to create **standardized endpoints** that AI models or tools can consume. Each mini-project in this repo demonstrates a different database backend.

### 🏗 Architecture Diagram

```
    +----------------+
    |                |
    |    LLM / AI    |
    |                |
    +--------+-------+
             |
             v
    +----------------+
    | FastMCP Server |
    |  (Python MCP)  |
    +--------+-------+
             |
             v
    +----------------+
    |Database Backend|
    | (MySQL, etc.)  |
    +----------------+
```
- **LLM / AI:** Your model or AI client (Claude, ChatGPT Pro, etc.) that queries the MCP. Some of them require the Desktop version.
- **FastMCP Server:** The MCP Python script that exposes resources and communicates via stdio or HTTP.  
- **Database Backend:** The actual data source (MySQL, Redis, Neo4j, HBase, etc.).

## 🧠 How To Run

Each of the databases in this repo have their own README.md file with detailed instructions on how to run the MCP on your machine!
Simply navigate to the folder and follow the steps to install dependencies and start the server.
Make sure you have the FastMCP Python library:
```bash
pip install fastmcp
```