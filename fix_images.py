#!/usr/bin/env python3
"""
Backfill has_image=True and image_path for questions where a PNG exists
in public/images/ but the question has has_image=False and image_path=None.
"""
import json
from pathlib import Path

IMAGES_DIR = Path("public/images")
QJ = Path("public/questions.json")

data = json.loads(QJ.read_text(encoding="utf-8"))
id_to_q = {q["id"]: q for q in data}

updated = []
orphaned = []

for png in sorted(IMAGES_DIR.glob("*.png")):
    qid = png.stem  # e.g. "2016_q33"
    rel  = f"images/{png.name}"

    if qid not in id_to_q:
        orphaned.append(png.name)
        continue

    q = id_to_q[qid]
    if not q.get("has_image") and not q.get("image_path"):
        q["has_image"]   = True
        q["image_path"]  = rel
        updated.append(qid)

QJ.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

print(f"Updated {len(updated)} questions:")
for qid in updated:
    print(f"  {qid}")

print(f"\nTruly orphaned PNGs (no matching question ID) — {len(orphaned)} files:")
for name in orphaned:
    print(f"  {name}")
