from datetime import datetime
from typing import Any, Dict, List, Optional
from pymongo import MongoClient
from pymongo.errors import PyMongoError
import json
from bson import json_util
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
          MONGO_CLIENT = MongoClient(connection_string, serverSelectionTimeoutMS=5000, maxPoolSize=int(os.getenv("DB_POOL_SIZE", 5)))
          MONGO_CLIENT.admin.command('ping')
          DATABASE = MONGO_CLIENT[DB_CONFIG["database"]]
       else:
          connection_string = f"mongodb://{DB_CONFIG['host']}:{DB_CONFIG['port']}"
          MONGO_CLIENT = MongoClient(connection_string, serverSelectionTimeoutMS=5000, maxPoolSize=int(os.getenv("DB_POOL_SIZE", 5)))
          MONGO_CLIENT.admin.command('ping')
          DATABASE = MONGO_CLIENT[DB_CONFIG["database"]]
    except PyMongoError as e:
        log_error(f"Error initializing MongoDB connection: {e}")
        sys.exit(1)

def log_error(message: str):
    """Log error messages"""
    if ENABLE_QUERY_LOGGING:
        print(f"[ERROR] {datetime.now().isoformat()} - {message}")

# MCP Tools

@mcp.tool()
def get_collection_stats(collection: str) -> Dict[str, Any]:
    col = DATABASE[collection]
    sample = list(col.find().limit(5))
    stats = DATABASE.command("collstats", collection)
    return {
        "stats": stats,
        "sample_documents": json.loads(json_util.dumps(sample))
    }

@mcp.tool()
def execute_find_query(query: str) -> List[Dict[str, Any]]:
    """
    Execute a MongoDB find query on a specified collection and return the results.
    The query should be a JSON string with 'collection' and 'filter' fields.
    Example:
    {
        "collection": "restaurants",
        "filter": {"cuisine": "Italian"},
        "limit": 10
    }
    """
    try:
        query_dict = json.loads(query)
        collection_name = query_dict.get("collection")
        filter_criteria = query_dict.get("filter", {})
        limit = query_dict.get("limit", 10)

        if not collection_name or not isinstance(filter_criteria, dict):
            raise ValueError("Invalid query format")

        collection = DATABASE[collection_name]
        cursor = collection.find(filter_criteria).limit(limit)
        results = list(cursor)
        return json.loads(json_util.dumps(results))
    except (json.JSONDecodeError, PyMongoError, ValueError) as e:
        log_error(f"Error executing select query: {e}")
        return []

@mcp.tool()
def execute_aggregate(params: str) -> List[Dict[str, Any]]:
    """
    Execute a MongoDB aggregation pipeline on a specified collection and return the results.
    The params should be a JSON string with 'collection' and 'pipeline' fields.
    Example:
    {
        "collection": "restaurants",
        "pipeline": [
            {"$match": {"cuisine": "Italian"}},
            {"$group": {"_id": "$borough", "count": {"$sum": 1}}}
        ],
        "limit": 10
    }
    """
    try:
        data = json.loads(params)
        col = data["collection"]
        pipeline = data["pipeline"]
        limit = data.get("limit", 50)

        for stage in pipeline:
            if "$out" in stage or "$merge" in stage:
                raise ValueError("Write operations not allowed")

        if limit:
            pipeline = pipeline + [{"$limit": limit}]

        cursor = DATABASE[col].aggregate(pipeline, maxTimeMS=MAX_QUERY_TIME)
        results = list(cursor)
        return json.loads(json_util.dumps(results))

    except Exception as e:
        log_error(f"Aggregation error: {str(e)}")
        return []


@mcp.tool()
def get_collection_schema(collection: str, sample_size: int = 100) -> dict:
    """
    Analyze a collection and return its schema by sampling documents.
    Returns field names, types, and example values.
    """
    try:
        sample = list(DATABASE[collection].aggregate([
            {"$sample": {"size": sample_size}},
            {"$limit": sample_size}
        ]))
        
        if not sample:
            return {"error": "Collection is empty"}
        
        schema = {}
        for doc in sample:
            for key, value in doc.items():
                if key not in schema:
                    schema[key] = {
                        "field": key,
                        "types": set(),
                        "sample_values": []
                    }
                
                schema[key]["types"].add(type(value).__name__)
                if len(schema[key]["sample_values"]) < 3:
                    schema[key]["sample_values"].append(str(value)[:50])
        
        result = []
        for field_info in schema.values():
            result.append({
                "field": field_info["field"],
                "types": list(field_info["types"]),
                "sample_values": field_info["sample_values"]
            })
        
        return {
            "collection": collection,
            "total_fields": len(result),
            "fields": result
        }
    
    except Exception as e:
        log_error(f"Schema analysis error: {str(e)}")
        return {"error": str(e)}


if __name__ == "__main__":
    init_connection()
    mcp.run()