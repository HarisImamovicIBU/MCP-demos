import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from contextlib import contextmanager
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from bson import json_util
import json
from fastmcp import FastMCP
import os
import sys
import re

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 27017)),
    "username": os.getenv("DB_USER", ""),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "sample_restaurants")
}

# Safety variables
MAX_QUERY_TIME = int(os.getenv("MAX_QUERY_TIME", 30000))
MAX_ROWS = int(os.getenv("MAX_ROWS", 10000))
ENABLE_QUERY_LOGGING = os.getenv("ENABLE_QUERY_LOGGING", "true").lower() == "true"

MONGO_CLIENT = None
DATABASE = None

mcp = FastMCP(
    name="MongoDB MCP",
    stateless_http=True,
    instructions="""
    This MCP server provides read-only access to the sample_restaurants MongoDB database.
    Available capabilities:
    - List all collections in the database
    - View collection schemas and sample documents
    - Execute find queries with filters
    - Perform aggregations
    - Search documents

    Security: Only read operations (find, aggregate, count) are allowed.
    All write operations are blocked for safety.
    """
)

# Utils

def init_connection():
    """Initialize MongoDB connection"""
    global MONGO_CLIENT, DATABASE
    try:
       if DB_CONFIG["username"] and DB_CONFIG["password"]:
          connection_string = f"mongodb://{DB_CONFIG['username']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}"
       else:
          connection_string = f"mongodb://{DB_CONFIG['host']}:{DB_CONFIG['port']}"
          MONGO_CLIENT = MongoClient(connection_string, serverSelectionTimeoutMS=5000, maxPoolSize=int(os.getenv("DB_POOL_SIZE", 5)))
          MONGO_CLIENT.admin.command('ping')  # Test connection
          DATABASE = MONGO_CLIENT[DB_CONFIG["database"]]
    except PyMongoError as e:
        log_error(f"Error initializing MongoDB connection: {e}")
        sys.exit(1)