"""
Load users.csv into MongoDB with auto-type casting and batch inserts.
"""
import argparse
import csv
import os
from typing import Any, Dict, Iterable, List

from pymongo import MongoClient


def auto_cast(value: str) -> Any:
    """Cast CSV string to int/float/bool/None or keep as string"""
    if value is None:
        return None
    s = value.strip()
    if s == "":
        return None
    
    lower = s.lower()
    if lower in {"true", "false"}:
        return lower == "true"
    
    try:
        if s.isdigit() or (s.startswith("-") and s[1:].isdigit()):
            return int(s)
    except ValueError:
        pass
    
    try:
        return float(s)
    except ValueError:
        pass
    
    return s


def batched(iterable: Iterable[Dict[str, Any]], n: int) -> Iterable[List[Dict[str, Any]]]:
    """Yield batches of size n from an iterable"""
    batch: List[Dict[str, Any]] = []
    for item in iterable:
        batch.append(item)
        if len(batch) >= n:
            yield batch
            batch = []
    if batch:
        yield batch


def import_csv_to_mongo(
    csv_path: str,
    mongo_uri: str,
    db_name: str,
    collection_name: str,
    batch_size: int = 1000,
    drop: bool = False,
) -> int:
    """
    Import CSV records into MongoDB with auto-type casting.
    Returns number of documents inserted.
    """
    if not os.path.isfile(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    client = MongoClient(mongo_uri)
    db = client[db_name]
    coll = db[collection_name]

    if drop:
        print(f"Dropping collection {db_name}.{collection_name}")
        coll.drop()

    inserted = 0
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        
        def doc_stream() -> Iterable[Dict[str, Any]]:
            for row in reader:
                doc: Dict[str, Any] = {k: auto_cast(v) for k, v in row.items()}
                yield doc

        for batch in batched(doc_stream(), max(1, batch_size)):
            if not batch:
                continue
            try:
                result = coll.insert_many(batch, ordered=False)
                inserted += len(result.inserted_ids)
            except Exception as e:
                # Retry individually on batch failure
                for doc in batch:
                    try:
                        coll.insert_one(doc)
                        inserted += 1
                    except Exception:
                        pass

    client.close()
    return inserted


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Import CSV file into MongoDB")
    p.add_argument("--uri", default="mongodb://localhost:27017", help="MongoDB URI (default: %(default)s)")
    p.add_argument("--db", default="aimat", help="Database name (default: %(default)s)")
    p.add_argument("--collection", "-c", default="users", help="Collection name (default: %(default)s)")
    p.add_argument("--file", "-f", default="users.csv", help="CSV file path (default: %(default)s)")
    p.add_argument("--batch-size", type=int, default=1000, help="Batch size (default: %(default)s)")
    p.add_argument("--drop", action="store_true", help="Drop collection before import")
    return p


def main() -> None:
    args = build_arg_parser().parse_args()
    
    print(f"Importing {args.file} into {args.db}.{args.collection}")
    
    inserted = import_csv_to_mongo(
        csv_path=args.file,
        mongo_uri=args.uri,
        db_name=args.db,
        collection_name=args.collection,
        batch_size=args.batch_size,
        drop=args.drop,
    )
    
    print(f"✓ Inserted {inserted} documents into {args.db}.{args.collection}")


if __name__ == "__main__":
    main()
