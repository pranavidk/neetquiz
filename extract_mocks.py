#!/usr/bin/env python3
"""
NEET Mock Test Extractor
Extracts questions, answers, and solutions from ALLEN mock test PDFs.
Outputs to mock_questions.json — does NOT touch questions.json.

Run:
    python extract_mocks.py

Verify the per-PDF summary, then run merge_mocks.py to merge into questions.json.
"""

import fitz
import re
import json
from pathlib import Path
from typing import Optional

PDFS_DIR    = Path("/Users/pranavshankar/neet-quiz/pdfs")
OUTPUT_JSON = Path("mock_questions.json")

MAX_Q = 180  # 180 questions per mock: Physics 1-45, Chemistry 46-90, Biology 91-180

# ── Shared regex (identical to extract_neet.py) ───────────────────────────────

IMAGE_KEYWORDS_RE = re.compile(
    r"\b(figure|circuit|diagram|graph|shown in|given below|"
    r"the figure|following figure|figure shows|waveform|"
    r"drawn|sketch|plot|charge distribution)\b",
    re.IGNORECASE,
)

Q_NUM_RE      = re.compile(r"(?m)^(\d{1,3})\.\s")
OPT_SPLIT_RE  = re.compile(r"\n *\(([1-4])\) *")

_ARTIFACT_RE = re.compile(
    r"NEET\(UG\)\s*[-–]\s*\d{4}|"
    r"\n\s*\d{1,3}\s*\n+\s*[A-Z]\s*\n|"
    r"[-�]",
)
_PAGE_NUM_TAIL_RE     = re.compile(r"\s+\d{1,2}\s+E\s*$")
_STACKED_FRACTION_RE  = re.compile(r"^\s*(\d+)\n\s*(\d+)\s*$")


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_subject(n: int) -> str:
    if n <= 45:  return "Physics"
    if n <= 90:  return "Chemistry"
    return "Biology"


def normalize(s: str) -> str:
    s = _ARTIFACT_RE.sub(" ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return _PAGE_NUM_TAIL_RE.sub("", s).strip()


def _normalize_option(raw_body: str) -> str:
    pre = _ARTIFACT_RE.sub(" ", raw_body)
    pre = _PAGE_NUM_TAIL_RE.sub("", pre).strip()
    m = _STACKED_FRACTION_RE.match(pre)
    if m and not pre[m.end():].strip():
        return f"{m.group(1)}/{m.group(2)}"
    return normalize(raw_body)


def page_text(doc: fitz.Document, start: int, end: int) -> str:
    return "\n".join(doc[i].get_text("text") for i in range(start, end))


def detect_ak_page(doc: fitz.Document) -> Optional[int]:
    """
    Find the answer key page: first page that contains both 'Que.' and 'Ans.'
    with a numeric grid of at least 10 digit tokens.
    Works for the vertical ('Que.' alone on a line) and inline ('Que. 1 2 3…')
    layouts found in ALLEN PDFs.
    """
    for i in range(len(doc)):
        text = doc[i].get_text("text")
        if "Que." in text and "Ans." in text:
            if len(re.findall(r"\b\d+\b", text)) >= 10:
                return i
    return None


# ── Parsers (same logic as extract_neet.py, year-agnostic) ───────────────────

def parse_questions(full_text: str) -> dict[int, dict]:
    questions: dict[int, dict] = {}
    matches = list(Q_NUM_RE.finditer(full_text))

    for idx, m in enumerate(matches):
        q_num = int(m.group(1))
        if not (1 <= q_num <= MAX_Q):
            continue

        body_start = m.end()
        body_end   = matches[idx + 1].start() if idx + 1 < len(matches) else len(full_text)
        chunk      = full_text[body_start:body_end]

        parts  = OPT_SPLIT_RE.split(chunk)
        q_text = normalize(parts[0])
        options = [""] * 4

        i = 1
        while i + 1 < len(parts):
            label, body = parts[i], parts[i + 1]
            if label.isdigit() and 1 <= int(label) <= 4:
                options[int(label) - 1] = _normalize_option(body)
            i += 2

        has_image = bool(IMAGE_KEYWORDS_RE.search(q_text)) or any(o == "" for o in options)
        questions[q_num] = {"q_text": q_text, "options": options, "has_image": has_image}

    # Fallback for questions without a trailing period (rare in some print runs)
    for q_num in range(1, MAX_Q + 1):
        if q_num in questions:
            continue
        fb = re.compile(rf"(?m)^{q_num} +(?=[A-Z])")
        fm = fb.search(full_text)
        if not fm:
            continue
        body_start = fm.end()
        next_m     = Q_NUM_RE.search(full_text, fm.end())
        body_end   = next_m.start() if next_m else len(full_text)
        chunk      = full_text[body_start:body_end]
        parts      = OPT_SPLIT_RE.split(chunk)
        q_text     = normalize(parts[0])
        options    = [""] * 4
        i = 1
        while i + 1 < len(parts):
            label, body = parts[i], parts[i + 1]
            if label.isdigit() and 1 <= int(label) <= 4:
                options[int(label) - 1] = _normalize_option(body)
            i += 2
        questions[q_num] = {
            "q_text":    q_text,
            "options":   options,
            "has_image": bool(IMAGE_KEYWORDS_RE.search(q_text)),
        }

    return questions


def parse_answer_key(doc: fitz.Document, ak_page: int) -> dict[int, int]:
    lines = [l.strip() for l in doc[ak_page].get_text("text").splitlines() if l.strip()]

    answers: dict[int, int] = {}
    i = 0
    while i < len(lines):
        line = lines[i]

        # Inline format: "Que. 1 2 3 …" on one line
        if re.match(r"^Que\.\s+\d+", line):
            que_nums = [int(x) for x in line.split()[1:] if x.isdigit()]
            j = i + 1
            while j < len(lines) and lines[j] != "Ans.":
                if lines[j].isdigit():
                    que_nums.append(int(lines[j]))
                j += 1
            if j < len(lines) and lines[j] == "Ans.":
                j += 1
                for qn in que_nums:
                    if j >= len(lines):
                        break
                    v = lines[j].strip()
                    if re.match(r"^[1-4]", v):
                        answers[qn] = int(v[0])
                    j += 1
            i = j
            continue

        # Vertical format: "Que." alone on a line
        if line == "Que.":
            que_nums = []
            j = i + 1
            while j < len(lines) and lines[j] != "Ans.":
                if lines[j].isdigit():
                    que_nums.append(int(lines[j]))
                j += 1
            if j < len(lines) and lines[j] == "Ans.":
                j += 1
                for qn in que_nums:
                    if j >= len(lines):
                        break
                    v = lines[j].strip()
                    if re.match(r"^[1-4]", v):
                        answers[qn] = int(v[0])
                    j += 1
            i = j
            continue

        i += 1

    return answers


def parse_solutions(doc: fitz.Document, sol_start: int, sol_end: int) -> dict[int, str]:
    full_text = page_text(doc, sol_start, sol_end)
    solutions: dict[int, str] = {}

    matches = list(Q_NUM_RE.finditer(full_text))
    for idx, m in enumerate(matches):
        q_num = int(m.group(1))
        if not (1 <= q_num <= MAX_Q):
            continue
        if q_num in solutions:   # first-occurrence-wins; skip chemistry sub-items
            continue
        body_start = m.end()
        body_end   = matches[idx + 1].start() if idx + 1 < len(matches) else len(full_text)
        sol_text   = normalize(full_text[body_start:body_end])
        if sol_text:
            solutions[q_num] = sol_text

    return solutions


# ── Per-mock orchestration ────────────────────────────────────────────────────

def extract_mock(pdf_path: Path, mock_num: int) -> list[dict]:
    print(f"\n{'─' * 58}")
    print(f"  MOCK-{mock_num}  |  {pdf_path.name}")

    doc         = fitz.open(str(pdf_path))
    total_pages = len(doc)

    ak_page = detect_ak_page(doc)
    if ak_page is None:
        print(f"  ERROR — could not detect answer key page. Skipping.")
        doc.close()
        return []

    q_start, q_end     = 0, ak_page
    sol_start, sol_end = ak_page, total_pages

    print(f"  Pages: {total_pages}  |  Q: 1–{ak_page}  |  AK: {ak_page + 1}  |  Sol: {ak_page + 1}–{total_pages}")
    print(f"{'─' * 58}")

    full_q_text = page_text(doc, q_start, q_end)
    questions   = parse_questions(full_q_text)
    print(f"  Questions parsed : {len(questions)}")

    answers = parse_answer_key(doc, ak_page)
    print(f"  Answers parsed   : {len(answers)}")

    solutions = parse_solutions(doc, sol_start, sol_end)
    print(f"  Solutions parsed : {len(solutions)}")

    records: list[dict] = []
    missing: list[int]  = []
    year_str = f"MOCK-{mock_num}"

    for q_num in range(1, MAX_Q + 1):
        if q_num not in questions:
            missing.append(q_num)
            continue

        q = questions[q_num]
        records.append({
            "id":             f"mock{mock_num}_q{q_num}",
            "year":           year_str,
            "q_number":       q_num,
            "subject":        get_subject(q_num),
            "text":           q["q_text"],
            "options":        q["options"],
            "correct_answer": answers.get(q_num),
            "solution":       solutions.get(q_num, ""),
            "has_image":      q["has_image"],
            "image_path":     None,
            "source":         "mock",
        })

    if missing:
        preview = missing[:20]
        suffix  = f" … (+{len(missing) - 20} more)" if len(missing) > 20 else ""
        print(f"  WARNING — not found: {preview}{suffix}")

    img_count = sum(1 for r in records if r["has_image"])
    print(f"  Records built    : {len(records)}  (image-flagged: {img_count})")

    doc.close()
    return records


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    all_records: list[dict] = []

    for mock_num in range(1, 10):
        # Handle both "MOCK TEST-N.pdf" (space) and "MOCK_TEST-N.pdf" (underscore)
        for name in (f"MOCK TEST-{mock_num}.pdf", f"MOCK_TEST-{mock_num}.pdf"):
            pdf_path = PDFS_DIR / name
            if pdf_path.exists():
                break
        else:
            print(f"\nWARNING — no PDF found for MOCK-{mock_num} in {PDFS_DIR}, skipping.")
            continue

        records = extract_mock(pdf_path, mock_num)
        all_records.extend(records)

    print("\n" + "═" * 58)
    print(f"  TOTAL records across all mocks : {len(all_records)}")
    ans_present = sum(1 for r in all_records if r["correct_answer"] is not None)
    sol_present = sum(1 for r in all_records if r["solution"])
    print(f"  With correct answer            : {ans_present}")
    print(f"  With solution text             : {sol_present}")
    print("═" * 58)

    OUTPUT_JSON.write_text(
        json.dumps(all_records, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"\nSaved {len(all_records)} records → {OUTPUT_JSON}")
    print("Run merge_mocks.py after verifying the output.")


if __name__ == "__main__":
    main()
