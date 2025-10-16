"""Quick test of ChromaDB search"""
import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from pymongo import MongoClient

# Check API key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("ERROR: GEMINI_API_KEY not set")
    exit(1)

print("✓ API key found")

# Connect to MongoDB
print("Connecting to MongoDB...")
client = MongoClient("mongodb://localhost:27017/")
db = client["aimat"]
coll = db["users"]
count = coll.count_documents({})
print(f"✓ MongoDB connected: {count:,} users")

# Connect to ChromaDB
print("Connecting to ChromaDB...")
embeddings = GoogleGenerativeAIEmbeddings(
    model="models/text-embedding-004",
    google_api_key=api_key
)

vector_store = Chroma(
    collection_name="user_embeddings",
    embedding_function=embeddings,
    persist_directory="chroma_db",
)
print("✓ ChromaDB connected")

# Test search
print("\nTesting search for: 'educated caring partner'")
query = "educated caring partner from good family"
results = vector_store.similarity_search(query, k=3)

print(f"\n✓ Found {len(results)} results:")
for i, doc in enumerate(results, 1):
    print(f"\n{i}. User ID: {doc.metadata.get('user_id')}")
    print(f"   Content: {doc.page_content}")

print("\n✓ Search test complete!")
client.close()
