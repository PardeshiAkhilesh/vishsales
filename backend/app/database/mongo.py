from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "vishal_sales")

client = None
db = None

async def connect_db():
    global client, db
    MONGODB_URL = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    client = MongoClient(MONGODB_URL)
    db = client[MONGO_DB]
    print("✅ MongoDB Connected")

def get_client() -> MongoClient:
    global client
    if client is None:
        client = MongoClient(MONGO_URI)
    return client

def get_db():
    global db
    if db is None:
        get_client()
        db = client[MONGO_DB]
    return db

def close_client():
    global client
    if client is not None:
        try:
            client.close()
        finally:
            client = None

client = get_client()
db = client[MONGO_DB]