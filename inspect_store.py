"""
Inspect vector store (Chroma) and MongoDB indexes.
Prints:
- Chroma collection document count (number of stored embeddings)
- MongoDB users collection index list and total count
"""
import os
from typing import List

import chromadb
from pymongo import MongoClient

CHROMA_DIR = os.getenv("CHROMA_PERSIST_DIR", "chroma_db")
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "user_embeddings")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB = os.getenv("MONGO_DB", "aimat")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "users")


def get_chroma_count() -> int:
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    try:
        coll = client.get_collection(CHROMA_COLLECTION)
    except Exception:
        # If collection doesn't exist yet, count is 0
        return 0
    return coll.count()


def get_mongo_indexes() -> List[str]:
    client = MongoClient(MONGO_URI)
    try:
        coll = client[MONGO_DB][MONGO_COLLECTION]
        return [idx.get("name", "unknown") for idx in coll.list_indexes()]
    finally:
        client.close()


def main():
    print(f"Chroma persist dir: {CHROMA_DIR}")
    print(f"Chroma collection: {CHROMA_COLLECTION}")
    chroma_count = get_chroma_count()
    print(f"\n✓ Chroma embeddings stored: {chroma_count:,}")

    indexes = get_mongo_indexes()
    print(f"\nMongoDB: {MONGO_DB}.{MONGO_COLLECTION}")
    print(f"✓ Total indexes: {len(indexes)}")
    for name in indexes:
        print(f"  - {name}")


if __name__ == "__main__":
    main()
