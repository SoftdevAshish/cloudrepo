"""MongoDB connection (PyMongo). Configure with MONGO_URL and MONGO_DB_NAME."""

import threading

from fastapi import Depends
from pymongo import MongoClient
from pymongo.database import Database

from app.core.config import settings

_client: MongoClient | None = None
_lock = threading.Lock()


def get_mongo_client() -> MongoClient:
    """Return the shared client, creating it lazily (PyMongo clients are thread-safe)."""
    global _client  # noqa: PLW0603
    if _client is None:
        with _lock:
            if _client is None:
                _client = MongoClient(settings.mongo_url, serverSelectionTimeoutMS=3000)
    return _client


def get_mongo_db() -> Database:
    return get_mongo_client()[settings.mongo_db_name]


def get_mongo(db: Database = Depends(get_mongo_db)) -> Database:
    """FastAPI dependency: `db: Database = Depends(get_mongo)`."""
    return db


def ping_mongo() -> bool:
    get_mongo_client().admin.command("ping")
    return True


def close_mongo() -> None:
    global _client  # noqa: PLW0603
    with _lock:
        if _client is not None:
            _client.close()
            _client = None
