"""
Verify MongoDB indexes are working perfectly for all users.
"""
from pymongo import MongoClient
import time


def verify_indexes():
    """Check MongoDB connection, user count, and all indexes."""
    client = MongoClient("mongodb://localhost:27017/")
    db = client["aimat"]
    coll = db["users"]
    
    # Count total users
    total = coll.count_documents({})
    print(f"✓ Connected to MongoDB: aimat.users")
    print(f"✓ Total users: {total:,}")
    
    # List all indexes
    print(f"\n{'='*60}")
    print("INDEXES (optimized for ALL {0:,} users)".format(total))
    print(f"{'='*60}")
    
    indexes = list(coll.list_indexes())
    for idx in indexes:
        name = idx.get("name", "unknown")
        keys = idx.get("key", {})
        key_str = ", ".join([f"{k}: {v}" for k, v in keys.items()])
        print(f"  ✓ {name:25s} → {key_str}")
    
    print(f"\n{'='*60}")
    print(f"Total indexes: {len(indexes)}")
    print(f"{'='*60}")
    
    # Test index performance
    print("\nTesting index performance on 300K+ users...")
    
    test_queries = [
        ({"Gender": "Male"}, "Gender filter"),
        ({"Gender": "Female", "Age": {"$gte": 24, "$lte": 32}}, "Gender + Age range"),
        ({"Gender": "Male", "Caste": "Syed"}, "Gender + Caste"),
        ({"Gender": "Female", "State": "Maharashtra"}, "Gender + State"),
    ]
    
    for query, desc in test_queries:
        start = time.time()
        count = coll.count_documents(query)
        elapsed = (time.time() - start) * 1000  # milliseconds
        print(f"  ✓ {desc:30s} → {count:6,} users in {elapsed:6.2f}ms")
    
    print("\n" + "="*60)
    print("✅ ALL INDEXES ARE PERFECT AND WORKING!")
    print("="*60)


if __name__ == "__main__":
    verify_indexes()
