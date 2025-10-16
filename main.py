"""
FastAPI service for AI Matrimonial RAG (MongoDB + ChromaDB).

Endpoints:
- POST /users: Add a new user profile (Mongo insert) and upsert embedding into ChromaDB (no retraining needed).
- GET  /match: Hybrid search using query + scalar filters (Age, Caste, Sect, State, Marital_Status),
               defaults to opposite-gender matching and supports +/- age tolerance.

Requirements: GEMINI_API_KEY in environment, MongoDB running locally.
"""
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from bson import ObjectId
from bson.errors import InvalidId
import os
import time

from pymongo import MongoClient
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma


# ---------- Config ----------
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB = os.getenv("MONGO_DB", "aimat")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "users")

CHROMA_DIR = os.getenv("CHROMA_PERSIST_DIR", "chroma_db")
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "user_embeddings")

EMBED_MODEL = "models/text-embedding-004"


# ---------- App ----------
app = FastAPI(title="AI Matrimonial RAG API", version="0.3.0")

mongo_client: MongoClient | None = None
mongo_coll = None
embeddings = None
vector_store: Chroma | None = None


# ---------- Schemas ----------
class UserIn(BaseModel):
    Age: int
    Gender: str
    Marital_Status: Optional[str] = None
    Caste: Optional[str] = None
    Sect: Optional[str] = None
    State: Optional[str] = None
    About: Optional[str] = Field(None, description="Short description about the user")
    Partner_Preference: Optional[str] = Field(
        None, description="What kind of partner the user is seeking"
    )


class UserOut(BaseModel):
    _id: str
    Age: Optional[int] = None
    Gender: Optional[str] = None
    Marital_Status: Optional[str] = None
    Caste: Optional[str] = None
    Sect: Optional[str] = None
    State: Optional[str] = None
    content: Optional[str] = None


# ---------- Helpers ----------
def serialize_user(doc: Dict[str, Any]) -> Dict[str, Any]:
    d = dict(doc)
    if isinstance(d.get("_id"), ObjectId):
        d["_id"] = str(d["_id"])
    return d


def get_opposite_gender(gender: str) -> str:
    g = (gender or "").lower()
    if g == "male":
        return "Female"
    if g == "female":
        return "Male"
    return gender


def build_user_text(user: Dict[str, Any]) -> str:
    parts: List[str] = []
    # structured fields
    for field in ["Age", "Gender", "Marital_Status", "Caste", "Sect", "State"]:
        val = user.get(field)
        if val not in (None, ""):
            parts.append(f"{field.replace('_', ' ')} {val}")
    # free-text
    if user.get("About"):
        parts.append(f"About: {user['About']}")
    if user.get("Partner_Preference"):
        parts.append(f"Seeks: {user['Partner_Preference']}")
    return ", ".join(parts)


def upsert_user_embedding(user_id: str, text: str):
    # Use low-level delete to avoid duplicates, then upsert by id
    try:
        vector_store._collection.delete(where={"user_id": user_id})  # type: ignore[attr-defined]
    except Exception:
        pass
    vector_store.add_texts([text], metadatas=[{"user_id": user_id}], ids=[user_id])


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
    f: Dict[str, Any] = {}
    if caste:
        f["Caste"] = caste
    if sect:
        f["Sect"] = sect
    if gender:
        f["Gender"] = get_opposite_gender(gender) if match_opposite_gender else gender
    if marital_status:
        f["Marital_Status"] = marital_status
    if state:
        f["State"] = state
    if min_age is not None or max_age is not None:
        age = {}
        if min_age is not None:
            age["$gte"] = min_age
        if max_age is not None:
            age["$lte"] = max_age
        f["Age"] = age
    return f


def hybrid_search(
    query_text: str,
    mongo_coll,
    top_k: int,
    mongo_filter: Optional[Dict[str, Any]],
):
    docs_cursor = mongo_coll.find(mongo_filter or {}, {"_id": 1})
    candidate_ids = [str(d["_id"]) for d in docs_cursor]
    if not candidate_ids:
        return [], 0

    MAX_IN = 900

    def _chunked(seq, n):
        for i in range(0, len(seq), n):
            yield seq[i : i + n]

    docs = []
    if len(candidate_ids) <= MAX_IN:
        docs_scores = vector_store.similarity_search_with_score(
            query_text,
            k=min(top_k, len(candidate_ids)),
            filter={"user_id": {"$in": candidate_ids}},
        )
        docs = [d for d, _ in docs_scores]
    else:
        best_by_user: Dict[str, tuple] = {}
        for chunk in _chunked(candidate_ids, MAX_IN):
            part = vector_store.similarity_search_with_score(
                query_text,
                k=min(top_k, len(chunk)),
                filter={"user_id": {"$in": chunk}},
            )
            for doc, score in part:
                uid = doc.metadata.get("user_id")
                if not uid:
                    continue
                # Keep best (lowest distance) score per user
                prev = best_by_user.get(uid)
                if prev is None or score < prev[1]:
                    best_by_user[uid] = (doc, score)
        docs = [d for d, _ in sorted(best_by_user.values(), key=lambda x: x[1])[:top_k]]
    results = []
    for doc in docs:
        uid = doc.metadata.get("user_id")
        if uid:
            u = mongo_coll.find_one({"_id": ObjectId(uid)})
            if u:
                u = serialize_user(u)
                u["content"] = doc.page_content
                results.append(u)
    return results, len(candidate_ids)

@app.on_event("startup")
def on_startup():
    global mongo_client, mongo_coll, embeddings, vector_store

    api_key = "AIzaSyBZmHqk_2uAvbk3DdzF4A4Rh9OpaVgf_SI"#os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")

    mongo_client = MongoClient(MONGO_URI)
    mongo_coll = mongo_client[MONGO_DB][MONGO_COLLECTION]

    embeddings = GoogleGenerativeAIEmbeddings(model=EMBED_MODEL, google_api_key=api_key)
    vector_store = Chroma(
        collection_name=CHROMA_COLLECTION,
        embedding_function=embeddings,
        persist_directory=CHROMA_DIR,
    )


@app.on_event("shutdown")
def on_shutdown():
    if mongo_client:
        mongo_client.close()


# ---------- Endpoints ----------
@app.get("/health")
def health():
    # quick ping for both stores
    total = mongo_coll.count_documents({})
    return {"status": "ok", "users": total, "chroma_collection": CHROMA_COLLECTION}


@app.post("/users", response_model=Dict[str, str])
def add_user(user: UserIn):
    """Add a user and upsert embedding to ChromaDB."""
    doc = user.model_dump()
    res = mongo_coll.insert_one(doc)
    uid = str(res.inserted_id)
    # Build and upsert embedding text
    text = build_user_text({**doc, "_id": uid})
    upsert_user_embedding(uid, text)
    return {"user_id": uid}


@app.get("/match", response_model=Dict[str, Any])
def match(
    query: Optional[str] = Query(None, description="Free-text preference. If omitted and user_id provided, uses user's Partner_Preference or About."),
    user_id: Optional[str] = Query(None, description="Requester user id to derive opposite gender and age range."),
    gender: Optional[str] = Query(None, description="Your gender (Male/Female); default: derived from user_id if provided."),
    same_gender: bool = Query(False, description="Match same gender instead of opposite."),
    caste: Optional[str] = None,
    sect: Optional[str] = None,
    marital_status: Optional[str] = None,
    state: Optional[str] = None,
    min_age: Optional[int] = None,
    max_age: Optional[int] = None,
    age_tolerance: int = Query(5, ge=0, le=20, description="If user_id provided and no explicit ages, uses user's age ± tolerance."),
    top_k: int = Query(10, ge=1, le=50),
):
    # Use user_id to infer defaults
    requester = None
    if user_id:
        try:
            obj_id = ObjectId(user_id)
        except InvalidId:
            raise HTTPException(status_code=400, detail="Invalid user_id format")
        requester = mongo_coll.find_one({"_id": obj_id})
        if not requester:
            raise HTTPException(status_code=404, detail="user_id not found")
        if gender is None:
            gender = requester.get("Gender")
        if min_age is None and max_age is None and requester.get("Age") is not None:
            age = int(requester["Age"])  # type: ignore
            min_age = max(18, age - age_tolerance)
            max_age = age + age_tolerance
        if query is None:
            # use their stated preference or about as the vector query
            query = requester.get("Partner_Preference") or requester.get("About") or ""

    if not query:
        query = "looking for suitable partner"

    mongo_filter = build_mongo_filter(
        caste=caste,
        sect=sect,
        gender=gender,
        marital_status=marital_status,
        state=state,
        min_age=min_age,
        max_age=max_age,
        match_opposite_gender=not same_gender,
    )

    start = time.time()
    results, candidate_count = hybrid_search(
        query_text=query,
        mongo_coll=mongo_coll,
        top_k=top_k,
        mongo_filter=mongo_filter,
    )
    elapsed = time.time() - start

    return {
        "query": query,
        "filters": mongo_filter,
        "candidates": candidate_count,
        "took_ms": round(elapsed * 1000, 2),
        "results": results,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
# Run with: uvicorn main:app --reload
