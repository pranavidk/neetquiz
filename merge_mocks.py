#!/usr/bin/env python3
"""
Merge mock_questions.json into public/questions.json.
Checks for duplicate IDs before writing. Safe to re-run — aborts on any collision.

Run ONLY after verifying extract_mocks.py output looks correct.
"""

import json
from pathlib import Path

QUESTIONS_JSON = Path("public/questions.json")
MOCK_JSON      = Path("mock_questions.json")


def main() -> None:
    if not QUESTIONS_JSON.exists():
        print(f"ERROR — {QUESTIONS_JSON} not found.")
        return
    if not MOCK_JSON.exists():
        print(f"ERROR — {MOCK_JSON} not found. Run extract_mocks.py first.")
        return

    existing = json.loads(QUESTIONS_JSON.read_text(encoding="utf-8"))
    mocks    = json.loads(MOCK_JSON.read_text(encoding="utf-8"))

    existing_ids = {r["id"] for r in existing}
    duplicates   = [r["id"] for r in mocks if r["id"] in existing_ids]

    if duplicates:
        print(f"ERROR — {len(duplicates)} duplicate ID(s) found. Aborting.")
        for d in duplicates[:20]:
            print(f"  {d}")
        if len(duplicates) > 20:
            print(f"  … and {len(duplicates) - 20} more")
        return

    # Per-mock summary before writing
    from collections import Counter
    sources = Counter(r["year"] for r in mocks)
    print("Mock questions to be added:")
    for year in sorted(sources):
        print(f"  {year} : {sources[year]} questions")

    merged = existing + mocks
    QUESTIONS_JSON.write_text(
        json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"\nMerged: {len(existing)} existing + {len(mocks)} mock = {len(merged)} total")
    print(f"Saved → {QUESTIONS_JSON}")


if __name__ == "__main__":
    main()
