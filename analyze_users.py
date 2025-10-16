import argparse
import json
from collections import defaultdict
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from pymongo import MongoClient


def _connect(uri: str, db: str, collection: str):
    client = MongoClient(uri)
    return client, client[db][collection]


def _count_total(coll) -> int:
    return coll.count_documents({})


def _count_missing(coll, field: str, consider_empty_missing: bool) -> int:
    if consider_empty_missing:
        missing_filter = {
            "$or": [
                {field: {"$exists": False}},
                {field: None},
                {field: ""},
            ]
        }
    else:
        missing_filter = {"$or": [{field: {"$exists": False}}, {field: None}]}
    return coll.count_documents(missing_filter)


def _value_counts(coll, field: str, top_n: int, consider_empty_missing: bool) -> List[Dict[str, Any]]:
    match_cond: Dict[str, Any]
    if consider_empty_missing:
        match_cond = {"$and": [{field: {"$exists": True}}, {field: {"$ne": None}}, {field: {"$ne": ""}}]}
    else:
        match_cond = {"$and": [{field: {"$exists": True}}, {field: {"$ne": None}}]}

    pipeline = [
        {"$match": match_cond},
        {"$group": {"_id": f"${field}", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    if top_n > 0:
        pipeline.append({"$limit": top_n})

    results: List[Dict[str, Any]] = []
    for doc in coll.aggregate(pipeline, allowDiskUse=True):
        # Keep value as-is; ensure it's JSON-serializable where possible
        value = doc.get("_id")
        results.append({"value": value, "count": doc.get("count", 0)})
    return results


def _distinct_count(coll, field: str, consider_empty_missing: bool) -> int:
    if consider_empty_missing:
        values = coll.distinct(field, {"$and": [{field: {"$exists": True}}, {field: {"$ne": None}}, {field: {"$ne": ""}}]})
    else:
        values = coll.distinct(field, {"$and": [{field: {"$exists": True}}, {field: {"$ne": None}}]})
    return len(values)


def _sample_keys_for_auto_detect(coll, sample_size: int = 500) -> Dict[str, Set[Any]]:
    """Return observed unique values per field from a small sample to detect categorical fields."""
    observed: Dict[str, Set[Any]] = defaultdict(set)
    for doc in coll.find({}, limit=sample_size):
        for k, v in doc.items():
            if k == "_id":
                continue
            # Track simple scalars only
            if isinstance(v, (str, int, float, bool)) or v is None:
                # Normalize empties to a placeholder to count as a distinct value if present
                observed[k].add(v if v not in ("",) else "")
    return observed


def _auto_detect_fields(coll, max_unique: int = 50, sample_size: int = 500) -> List[str]:
    observed = _sample_keys_for_auto_detect(coll, sample_size=sample_size)
    # Favor common categorical names first
    preferred = ["marital_status", "maritalStatus", "caste", "gender"]
    candidates: List[Tuple[int, str]] = []
    for k, values in observed.items():
        uniq = len(values)
        if 1 < uniq <= max_unique:
            priority = 0 if k in preferred else 1
            candidates.append((priority, k))
    candidates.sort()
    # Return up to 10 fields by default
    return [k for _, k in candidates][:10]


def analyze(
    uri: str,
    db: str,
    collection: str,
    fields: Optional[List[str]] = None,
    auto_detect: bool = False,
    top_n: int = 10,
    consider_empty_missing: bool = True,
) -> Dict[str, Any]:
    client, coll = _connect(uri, db, collection)
    try:
        total = _count_total(coll)

        use_fields: List[str]
        if fields:
            use_fields = fields
        elif auto_detect:
            use_fields = _auto_detect_fields(coll)
        else:
            # Default common categorical fields
            use_fields = ["marital_status", "caste", "gender"]

        summary: Dict[str, Any] = {
            "total": total,
            "fields": {},
            "analyzed_fields": use_fields,
        }
        for f in use_fields:
            try:
                top = _value_counts(coll, f, top_n=top_n, consider_empty_missing=consider_empty_missing)
                distinct = _distinct_count(coll, f, consider_empty_missing=consider_empty_missing)
                missing = _count_missing(coll, f, consider_empty_missing=consider_empty_missing)
                summary["fields"][f] = {
                    "top": top,
                    "distinct_count": distinct,
                    "missing_count": missing,
                }
            except Exception as e:
                summary["fields"][f] = {"error": str(e)}

        return summary
    finally:
        client.close()


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Analyze user dataset in MongoDB and print summary stats")
    p.add_argument("--uri", default="mongodb://localhost:27017", help="MongoDB connection URI (default: %(default)s)")
    p.add_argument("--db", default="aimat", help="Database name (default: %(default)s)")
    p.add_argument("--collection", "-c", default="users", help="Collection name (default: %(default)s)")
    p.add_argument("--fields", nargs="*", help="Fields to analyze (space-separated). Omit to use defaults or --auto-detect")
    p.add_argument("--auto-detect", action="store_true", help="Auto-detect categorical fields from a sample")
    p.add_argument("--top-n", type=int, default=10, help="Show top N values per field (default: %(default)s)")
    p.add_argument("--include-empty", dest="consider_empty_missing", action="store_true", help="Treat empty strings as missing in counts (default)")
    p.add_argument("--keep-empty", dest="consider_empty_missing", action="store_false", help="Do not treat empty strings as missing")
    p.set_defaults(consider_empty_missing=True)
    p.add_argument("--output", choices=["json", "table"], default="json", help="Output format (default: %(default)s)")
    return p


def _print_table(summary: Dict[str, Any]) -> None:
    total = summary.get("total", 0)
    print(f"Total documents: {total}")
    analyzed_fields = summary.get("analyzed_fields", [])
    for f in analyzed_fields:
        data = summary["fields"].get(f, {})
        if "error" in data:
            print(f"\nField: {f}\n  Error: {data['error']}")
            continue
        print(f"\nField: {f}")
        print(f"  Distinct: {data.get('distinct_count', 0)} | Missing: {data.get('missing_count', 0)}")
        top = data.get("top", [])
        if not top:
            print("  No values.")
            continue
        # Compute col widths
        val_col = "Value"
        cnt_col = "Count"
        val_width = max(len(val_col), max((len(str(it.get('value'))) for it in top), default=0))
        cnt_width = max(len(cnt_col), max((len(str(it.get('count'))) for it in top), default=0))
        print(f"  {val_col:<{val_width}}  {cnt_col:>{cnt_width}}")
        print(f"  {'-'*val_width}  {'-'*cnt_width}")
        for it in top:
            print(f"  {str(it.get('value')):<{val_width}}  {str(it.get('count')):>{cnt_width}}")


def main() -> None:
    args = build_arg_parser().parse_args()
    summary = analyze(
        uri=args.uri,
        db=args.db,
        collection=args.collection,
        fields=args.fields,
        auto_detect=args.auto_detect,
        top_n=args.top_n,
        consider_empty_missing=args.consider_empty_missing,
    )
    if args.output == "json":
        print(json.dumps(summary, indent=2, default=str))
    else:
        _print_table(summary)


if __name__ == "__main__":
    main()
