#!/usr/bin/env python3
"""Backfill source: 'neet_pyq' on all questions that have no source field."""
import json
from pathlib import Path

PATH = Path("public/questions.json")
data = json.loads(PATH.read_text(encoding="utf-8"))

updated = 0
for q in data:
    if "source" not in q:
        q["source"] = "neet_pyq"
        updated += 1

PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Updated {updated} questions with source='neet_pyq'")
print(f"Total questions: {len(data)}")
