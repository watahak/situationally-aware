"""Validate context JSON files for schema completeness and freshness.

Usage:
    python scripts/validate_contexts.py
"""

import json
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONTEXTS_DIR = PROJECT_ROOT / "contexts"
PROMPTS_DIR = PROJECT_ROOT / "prompts"

REQUIRED_ENVELOPE = [
    "schema_version",
    "context_type",
    "data_as_of",
    "retrieved_on",
    "freshness_days",
    "sources",
    "data",
]

VALID_CONTEXT_TYPES = {"structural", "seasonal", "tactical"}


def parse_retrieved_on(date_str: str) -> datetime | None:
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except (ValueError, TypeError):
        return None


def validate_one(path: Path, today: datetime) -> dict:
    result = {
        "name": path.stem,
        "type": "",
        "as_of": "",
        "retrieved": "",
        "age_days": None,
        "threshold": None,
        "status": "OK",
        "warnings": [],
    }

    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as e:
        result["status"] = "ERROR"
        result["warnings"].append(f"Cannot parse: {e}")
        return result

    missing = [f for f in REQUIRED_ENVELOPE if f not in data]
    if missing:
        result["warnings"].append(f"Missing envelope fields: {', '.join(missing)}")

    ctx_type = data.get("context_type", "")
    result["type"] = ctx_type
    if ctx_type and ctx_type not in VALID_CONTEXT_TYPES:
        result["warnings"].append(f"Invalid context_type: {ctx_type}")

    result["as_of"] = str(data.get("data_as_of", ""))
    result["retrieved"] = str(data.get("retrieved_on", ""))
    result["threshold"] = data.get("freshness_days")

    if data.get("data_as_of") is None:
        result["status"] = "EMPTY"
        result["warnings"].append("data_as_of is null (template not populated)")
        return result

    retrieved = parse_retrieved_on(data.get("retrieved_on"))
    if retrieved is None:
        result["status"] = "ERROR"
        result["warnings"].append(f"Cannot parse retrieved_on: {data.get('retrieved_on')}")
        return result

    age = (today - retrieved).days
    result["age_days"] = age
    threshold = data.get("freshness_days")

    if threshold is not None and age > threshold:
        result["status"] = "STALE"
    elif result["warnings"]:
        result["status"] = "WARN"

    return result


def main():
    today = datetime.now()

    context_files = sorted(CONTEXTS_DIR.glob("*.json")) if CONTEXTS_DIR.exists() else []
    prompt_files = sorted(PROMPTS_DIR.glob("*.md")) if PROMPTS_DIR.exists() else []

    context_stems = {p.stem for p in context_files}
    prompt_stems = {p.stem for p in prompt_files}

    orphan_contexts = context_stems - prompt_stems
    orphan_prompts = prompt_stems - context_stems

    results = [validate_one(p, today) for p in context_files]

    print(f"Context Validation Report — {today.strftime('%Y-%m-%d')}")
    print()
    print(f"{'Context':<30} {'Type':<12} {'As-Of':<12} {'Retrieved':<12} {'Age':<6} {'Threshold':<10} {'Status'}")
    print("-" * 100)

    for r in results:
        age_str = f"{r['age_days']}d" if r["age_days"] is not None else "-"
        thr_str = f"{r['threshold']}d" if r["threshold"] is not None else "-"
        print(f"{r['name']:<30} {r['type']:<12} {r['as_of']:<12} {r['retrieved']:<12} {age_str:<6} {thr_str:<10} {r['status']}")

    if orphan_prompts:
        print(f"\nMissing contexts (prompt exists, no JSON): {', '.join(sorted(orphan_prompts))}")
    if orphan_contexts:
        print(f"\nOrphaned contexts (no matching prompt): {', '.join(sorted(orphan_contexts))}")

    warnings = [(r["name"], w) for r in results for w in r["warnings"]]
    if warnings:
        print("\nWarnings:")
        for name, w in warnings:
            print(f"  {name}: {w}")

    if not orphan_prompts and not orphan_contexts and not warnings:
        print("\nNo issues found.")

    has_problems = any(r["status"] in ("STALE", "ERROR") for r in results) or orphan_prompts
    sys.exit(1 if has_problems else 0)


if __name__ == "__main__":
    main()
