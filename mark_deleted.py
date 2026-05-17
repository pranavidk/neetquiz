#!/usr/bin/env python3
"""
Mark questions from deleted NEET syllabus topics.
Adds is_deleted_topic: true/false to every record in questions.json.
Source: ALLEN Kota PYQ book, pages 11-13 (scanned table).
Years 2021-2025 not listed in the table → all false.
"""

import json
from pathlib import Path

QUESTIONS_JSON = Path("questions.json")

# Year → set of question numbers from deleted syllabus topics
DELETED_QUESTIONS: dict[int, set[int]] = {
    2020: {1, 9, 19, 46, 56, 63, 68, 72, 82, 85, 87, 88,
           98, 109, 110, 139, 141, 146, 147, 162, 179, 180},
    2019: {25, 27,                                          # Physics
           47, 52, 56, 58, 64, 71, 76, 77, 82, 85, 90,    # Chemistry
           94, 99, 106, 111, 115, 116, 117, 126, 139,      # Biology
           140, 145, 146, 148, 149, 155},
    2018: {6, 14, 24, 36,                                  # Physics
           48, 50, 59, 65, 68, 71, 75, 78,                 # Chemistry
           95, 98, 106, 107, 111, 126, 132, 134,           # Biology
           143, 150, 162, 177},
    2017: {2, 8, 19, 20, 24, 27, 41,                       # Physics
           58, 67, 70, 73, 86, 93,                         # Chemistry
           106, 112, 117, 134, 141, 148, 166, 173},        # Biology
    2016: {4, 11, 17, 31,                                  # Physics
           50, 52, 53, 57, 58, 65, 67, 68, 77, 79, 98,    # Chemistry
           104, 106, 127, 163, 164, 166, 171, 175, 178},   # Biology
}


def main() -> None:
    records: list[dict] = json.loads(QUESTIONS_JSON.read_text(encoding="utf-8"))

    flagged = 0
    for r in records:
        year: int = r["year"]
        q_num: int = r["q_number"]
        deleted_set = DELETED_QUESTIONS.get(year, set())
        is_deleted = q_num in deleted_set
        r["is_deleted_topic"] = is_deleted
        if is_deleted:
            flagged += 1

    QUESTIONS_JSON.write_text(
        json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    total = len(records)
    print(f"Processed {total} records.")
    print(f"Flagged {flagged} as is_deleted_topic=true, {total - flagged} as false.")

    # Summary by year
    from collections import defaultdict
    by_year: dict[int, int] = defaultdict(int)
    for r in records:
        if r["is_deleted_topic"]:
            by_year[r["year"]] += 1
    for yr in sorted(by_year):
        print(f"  {yr}: {by_year[yr]} deleted")


if __name__ == "__main__":
    main()
