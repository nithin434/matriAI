"""
Generate embeddings and sync to Milvus using LangChain.
Reads users from MongoDB, creates embeddings, stores in Milvus vector store.
"""
import argparse
import os
import time
from typing import Any, Dict, List

from langchain.docstore.document import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from pymongo import MongoClient


def connect_mongo(uri: str, db: str, collection: str):
    """Connect to MongoDB"""
    client = MongoClient(uri)
    return client, client[db][collection]


def build_user_text(user: Dict[str, Any], fields: List[str]) -> str:
    """
    Build text representation for embedding.
    Example: "Age 26, Male, Never Married, Sheikh caste, Sunni sect, Uttar Pradesh"
    """
    parts = []
    for field in fields:
        value = user.get(field)
        if value is not None and value != "":
            parts.append(f"{field.replace('_', ' ')} {value}")
    return ", ".join(parts)


def process_and_sync(
    mongo_coll,
    vector_store,
    fields: List[str],
    batch_size: int,
    limit: int,
) -> int:
    """
    Read users from MongoDB, create documents, add to Milvus.
    Returns number processed.
    """
    query = {}
    if limit > 0:
        total = min(mongo_coll.count_documents(query), limit)
    else:
        total = mongo_coll.count_documents(query)
    
    print(f"Processing {total} users")
    
    processed = 0
    cursor = mongo_coll.find(query)
    if limit > 0:
        cursor = cursor.limit(limit)
    
    batch_docs = []
    
    for user in cursor:
        # Build text content
        text = build_user_text(user, fields)
        user_id = str(user["_id"])
        
        # Create LangChain Document with metadata
        doc = Document(
            page_content=text,
            metadata={"user_id": user_id}
        )
        batch_docs.append(doc)
        
        if len(batch_docs) >= batch_size:
            vector_store.add_documents(batch_docs)
            processed += len(batch_docs)
            print(f"Progress: {processed}/{total} ({100*processed/total:.1f}%)")
            batch_docs = []
            time.sleep(0.5)  # Rate limiting
    
    if batch_docs:
        vector_store.add_documents(batch_docs)
        processed += len(batch_docs)
        print(f"Progress: {processed}/{total} (100.0%)")
    
    return processed


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Generate embeddings and sync to Milvus with LangChain")
    p.add_argument("--mongo-uri", default="mongodb://localhost:27017", help="MongoDB URI (default: %(default)s)")
    p.add_argument("--mongo-db", default="aimat", help="MongoDB database (default: %(default)s)")
    p.add_argument("--mongo-collection", default="users", help="MongoDB collection (default: %(default)s)")
    p.add_argument("--chroma-persist-dir", default="chroma_db", help="ChromaDB persist directory (default: %(default)s)")
    p.add_argument("--chroma-collection", default="user_embeddings", help="ChromaDB collection (default: %(default)s)")
    p.add_argument("--milvus-port", default="19530", help="Milvus port (default: %(default)s)")
    p.add_argument("--milvus-collection", default="user_embeddings", help="Milvus collection (default: %(default)s)")
    p.add_argument("--fields", nargs="+", default=["Age", "Gender", "Marital_Status", "Caste", "Sect", "State"],
                   help="Fields for embedding text (default: %(default)s)")
    p.add_argument("--batch-size", type=int, default=100, help="Batch size (default: %(default)s)")
    p.add_argument("--limit", type=int, default=0, help="Limit users (0=all, default: %(default)s)")
    return p


def main():
    args = build_arg_parser().parse_args()
    
    # Check API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: Set GEMINI_API_KEY env var")
        return
    
    # Initialize embeddings
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/text-embedding-004",
        google_api_key=api_key
    )
    
    # Connect to MongoDB
    print(f"Connecting to MongoDB: {args.mongo_db}.{args.mongo_collection}")
    mongo_client, mongo_coll = connect_mongo(args.mongo_uri, args.mongo_db, args.mongo_collection)
    
    # Connect to ChromaDB
    print(f"Connecting to ChromaDB: {args.chroma_collection} (persist dir: {args.chroma_persist_dir})")
    vector_store = Chroma(
        collection_name=args.chroma_collection,
        embedding_function=embeddings,
        persist_directory=args.chroma_persist_dir,
    )
    
    
    try:
        start = time.time()
        
        processed = process_and_sync(
            mongo_coll=mongo_coll,
            vector_store=vector_store,
            fields=args.fields,
            batch_size=args.batch_size,
            limit=args.limit,
        )
        
        elapsed = time.time() - start
        print(f"\n✓ Processed {processed} users in {elapsed:.1f}s ({processed/elapsed:.1f} users/sec)")
        
    finally:
        mongo_client.close()


if __name__ == "__main__":
    main()
