# mongo_loader.py
from dotenv import load_dotenv
from typing import Any, Dict, List, Optional
from pymongo import MongoClient
import os

load_dotenv()

class Mongo:
    def __init__(
        self,
        database: str,
        collection: str,
    ) -> None:
        """
        :param uri: MongoDB connection URI (e.g. "mongodb://user:pass@host:port/dbname")
        :param database: database name (e.g. "DropshipProducts")
        :param collection: collection name (e.g. "amazon_products")
        """
        self.client = MongoClient(
            os.getenv("MONGO_URI", "mongodb://localhost:27017")
        )
        self.db = self.client[database]
        self.coll = self.db[collection]

    def find(
        self, 
        filter: Optional[Dict[str, Any]] = None, 
        projection: Optional[Dict[str, int]] = None,
        limit: Optional[int] = None,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Run a .find() query.
        :param filter: Mongo filter dict (or None for all docs)
        :param projection: which fields to include/exclude
        :param limit: if set, only return up to this many docs
        :returns: list of document dicts
        """
        cursor = self.coll.find(filter or {}, projection or {})
        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)
        return list(cursor)

    def load_all(self) -> List[Dict[str, Any]]:
        """Load every document in the collection."""
        return self.find()
    
    