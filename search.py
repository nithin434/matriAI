"""
Hybrid RAG search using LangChain: MongoDB filters + Milvus vectors.
"""
import argparse
import os
import time
from typing import Any, Dict, List, Optional

from bson import ObjectId
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from pymongo import MongoClient


def connect_mongo(uri: str, db: str, collection: str):
    """Connect to MongoDB"""
    client = MongoClient(uri)
    return client, client[db][collection]


def get_opposite_gender(gender: str) -> str:
    """Get opposite gender for matching"""
    if gender.lower() == "male":
        return "Female"
    elif gender.lower() == "female":
        return "Male"
    return gender


def build_mongo_filter(
    caste: Optional[str],
    sect: Optional[str],
    gender: Optional[str],
    marital_status: Optional[str],
    state: Optional[str],
    min_age: Optional[int],
    max_age: Optional[int],
    match_opposite_gender: bool = True,
) -> Dict[str, Any]:
    """
    Build MongoDB query filter.
    If match_opposite_gender=True, searches for opposite gender (male -> female, female -> male)
    """
    mongo_filter = {}
    
    if caste:
        mongo_filter["Caste"] = caste
    if sect:
        mongo_filter["Sect"] = sect
    
    # For matching: search opposite gender
    if gender:
        if match_opposite_gender:
            mongo_filter["Gender"] = get_opposite_gender(gender)
            print(f"→ Searching for {get_opposite_gender(gender)} profiles (opposite of {gender})")
        else:
            mongo_filter["Gender"] = gender
    
    if marital_status:
        mongo_filter["Marital_Status"] = marital_status
    if state:
        mongo_filter["State"] = state
    
    if min_age is not None or max_age is not None:
        age_filter = {}
        if min_age is not None:
            age_filter["$gte"] = min_age
        if max_age is not None:
            age_filter["$lte"] = max_age
        mongo_filter["Age"] = age_filter
    
    return mongo_filter


def hybrid_search(
    query_text: str,
    mongo_coll,
    vector_store,
    top_k: int = 10,
    mongo_filter: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Hybrid search: vector similarity + MongoDB scalar filters.
    """
    # Strategy 1: With MongoDB prefilter
    if mongo_filter:
        # Get candidate user IDs
        candidate_docs = mongo_coll.find(mongo_filter, {"_id": 1})
        candidate_ids = [str(doc["_id"]) for doc in candidate_docs]
        
        if not candidate_ids:
            print("No users match the filters")
            return []
        
        print(f"Filtered to {len(candidate_ids)} candidates")
        
        # LangChain similarity search with metadata filter (Chroma)
        docs = vector_store.similarity_search(
            query_text,
            k=min(top_k, len(candidate_ids)),
            filter={"user_id": {"$in": candidate_ids}}
        )
    else:
        # Strategy 2: Pure vector search
        docs = vector_store.similarity_search(query_text, k=top_k)
    
    # Fetch full user data from MongoDB
    results = []
    for doc in docs:
        user_id = doc.metadata.get("user_id")
        if user_id:
            user_doc = mongo_coll.find_one({"_id": ObjectId(user_id)})
            if user_doc:
                user_doc["_id"] = str(user_doc["_id"])
                user_doc["content"] = doc.page_content
                results.append(user_doc)
    
    return results


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Hybrid search with LangChain: MongoDB + ChromaDB")
    p.add_argument("--query", required=True, help="Search query text")
    p.add_argument("--mongo-uri", default="mongodb://localhost:27017", help="MongoDB URI (default: %(default)s)")
    p.add_argument("--mongo-db", default="aimat", help="MongoDB database (default: %(default)s)")
    p.add_argument("--mongo-collection", default="users", help="MongoDB collection (default: %(default)s)")
    p.add_argument("--chroma-persist-dir", default="chroma_db", help="ChromaDB persist directory (default: %(default)s)")
    p.add_argument("--chroma-collection", default="user_embeddings", help="ChromaDB collection (default: %(default)s)")
    p.add_argument("--top-k", type=int, default=10, help="Number of results (default: %(default)s)")
    
    # Scalar filters
    p.add_argument("--caste", help="Filter by caste")
    p.add_argument("--sect", help="Filter by sect")
    p.add_argument("--gender", help="Your gender (searches for opposite gender matches)")
    p.add_argument("--marital-status", help="Filter by marital status")
    p.add_argument("--state", help="Filter by state")
    p.add_argument("--min-age", type=int, help="Minimum age")
    p.add_argument("--max-age", type=int, help="Maximum age")
    p.add_argument("--same-gender", action="store_true", help="Search same gender instead of opposite")
    
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

    # Build filter
    mongo_filter = build_mongo_filter(
        caste=args.caste,
        sect=args.sect,
        gender=args.gender,
        marital_status=args.marital_status,
        state=args.state,
        min_age=args.min_age,
        max_age=args.max_age,
        match_opposite_gender=not args.same_gender,
    )
    if mongo_filter:
        print(f"MongoDB filters: {mongo_filter}")

    # Search
    print(f"Searching for: '{args.query}'")
    start = time.time()
    results = hybrid_search(
        query_text=args.query,
        mongo_coll=mongo_coll,
        vector_store=vector_store,
        top_k=args.top_k,
        mongo_filter=mongo_filter,
    )
    elapsed = time.time() - start
    print(f"\nTop {len(results)} matches (searched in {elapsed:.2f}s):")
    for i, user in enumerate(results, 1):
        print(f"\n{i}. User ID: {user['_id']}")
        print(f"   {user.get('content', 'No content')}")
        print(f"   Age: {user.get('Age')}, Gender: {user.get('Gender')}, Caste: {user.get('Caste')}")
        print(f"   Marital Status: {user.get('Marital_Status')}, State: {user.get('State')}")

    mongo_client.close()


if __name__ == "__main__":
    main()
