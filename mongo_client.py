from pymongo import MongoClient
import certifi
from config import MONGO_URI

def get_mongo_client():
    """Create and return a MongoClient using TLS and certifi CA bundle."""
    return MongoClient(
        MONGO_URI,
        tls=True,
        tlsCAFile=certifi.where()
    )


def get_database(db_name: str = "sample_mflix"):
    """Return the specified database from the MongoDB client."""
    client = get_mongo_client()
    return client[db_name]