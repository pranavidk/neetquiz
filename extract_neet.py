#!/usr/bin/env python3
"""
NEET PYQ Extractor
Extracts questions, answers, and solutions from ALLEN Kota 10-year NEET PYQ PDF.
Run with 2025 only first; add remaining years once validated.
"""

import fitz
import re
import json
from pathlib import Path
from typing import Optional

PDF_PATH = "/Users/pranavshankar/Downloads/NEET-UG_10 years(2025-2016)_Eng.pdf"
IMAGES_DIR = Path("images")
OUTPUT_JSON = Path("questions.json")

IMAGES_DIR.mkdir(exist_ok=True)

# ── Year page configs (all 0-indexed PDF pages) ──────────────────────────────
# q_pages  : [start, end) range of question paper pages
# ak_page  : single page containing the Que./Ans. grid
# sol_pages: [start, end) range containing hints/solutions
#            (includes ak_page since Q1 solution starts there)
YEAR_CONFIG = {
    2025: {"q_pages": (12, 38),   "ak_page": 38,  "sol_pages": (38, 50)},
    2024: {"q_pages": (50, 76),   "ak_page": 76,  "sol_pages": (76, 88)},
    2023: {"q_pages": (88, 113),  "ak_page": 113, "sol_pages": (113, 124)},
    2022: {"q_pages": (124, 151), "ak_page": 151, "sol_pages": (151, 160)},
    2021: {"q_pages": (160, 182), "ak_page": 182, "sol_pages": (182, 192)},
    2020: {"q_pages": (192, 208), "ak_page": 208, "sol_pages": (208, 214)},
    2019: {"q_pages": (214, 232), "ak_page": 232, "sol_pages": (232, 240)},
    2018: {"q_pages": (240, 258), "ak_page": 258, "sol_pages": (258, 266)},
    2017: {"q_pages": (266, 282), "ak_page": 282, "sol_pages": (282, 290)},
    2016: {"q_pages": (290, 305), "ak_page": 305, "sol_pages": (305, 312)},
}

# Keywords in question text that indicate a diagram / figure is present
IMAGE_KEYWORDS_RE = re.compile(
    r"\b(figure|circuit|diagram|graph|shown in|given below|"
    r"the figure|following figure|figure shows|waveform|"
    r"drawn|sketch|plot|charge distribution)\b",
    re.IGNORECASE,
)

# "N.\s" at the start of any line — matches both "N.\n" (own line) and "N. text" (same line)
Q_NUM_RE = re.compile(r"(?m)^(\d{1,3})\.\s")

# "(N) " or "(N)\n" — option label separator
OPT_SPLIT_RE = re.compile(r"\n *\(([1-4])\) *")

# Page headers / decorative unicode that leak into question / option text
_ARTIFACT_RE = re.compile(
    r"NEET\(UG\)\s*[-–]\s*\d{4}|"      # "NEET(UG) - 2025"
    r"\n\s*\d{1,3}\s*\n+\s*[A-Z]\s*\n|"  # "2\n\nE\n" page-num + series (blank line ok)
    r"[-￿]",               # private-use unicode (decorative glyphs)
)
# Residual "28 E" / "2 E" after collapse — page-number + NEET series code at tail
_PAGE_NUM_TAIL_RE = re.compile(r"\s+\d{1,2}\s+E\s*$")


# ── Helpers ──────────────────────────────────────────────────────────────────

# Years that used the 200-question Section A/B format
_SECTION_B_YEARS = {2021, 2022, 2023, 2024}


def max_q_for_year(year: int) -> int:
    return 200 if year in _SECTION_B_YEARS else 180


def get_subject(n: int, year: int) -> str:
    if year in _SECTION_B_YEARS:
        if n <= 50:  return "Physics"
        if n <= 100: return "Chemistry"
        return "Biology"
    else:
        if n <= 45:  return "Physics"
        if n <= 90:  return "Chemistry"
        return "Biology"


def get_sub_subject(n: int, year: int) -> Optional[str]:
    """Return 'Botany' or 'Zoology' for 2021-2024 Biology questions, else None."""
    if year in _SECTION_B_YEARS and n > 100:
        return "Botany" if n <= 150 else "Zoology"
    return None


# Stacked fractions render as "numerator\ndenominator" in the PDF text layer —
# the fraction bar is a vector line, never a character.  When the RAW option body
# (before whitespace collapsing) contains exactly two bare integers separated by
# a newline (and optional surrounding whitespace), we restore the "/".
# Same-line cases like "100 2" are NOT fractions; they are "100√2" where √ is a
# drawn glyph — unrecoverable from text alone, so left as-is.
_STACKED_FRACTION_RE = re.compile(r"^\s*(\d+)\n\s*(\d+)\s*$")


def normalize(s: str) -> str:
    """Collapse whitespace / newlines and strip PDF page-header artifacts."""
    s = _ARTIFACT_RE.sub(" ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return _PAGE_NUM_TAIL_RE.sub("", s).strip()


def _normalize_option(raw_body: str) -> str:
    """Normalize option text; restore stacked-fraction '/' from raw body."""
    # Strip artifacts before the fraction check so page-header noise on the
    # same chunk (e.g. '\nNEET(UG)…') doesn't block the pattern.
    # Strip PDF artifacts and page-number tails before the fraction check so
    # trailing noise like '\n2\nE' (page-num + series) doesn't block the match.
    pre = _ARTIFACT_RE.sub(" ", raw_body)
    pre = _PAGE_NUM_TAIL_RE.sub("", pre).strip()
    m = _STACKED_FRACTION_RE.match(pre)
    if m and not pre[m.end():].strip():  # nothing remaining after the two integers
        return f"{m.group(1)}/{m.group(2)}"
    return normalize(raw_body)


def page_text(doc: fitz.Document, start: int, end: int) -> str:
    """Concatenate plain text from pages [start, end)."""
    return "\n".join(doc[i].get_text("text") for i in range(start, end))


# ── Question parser ───────────────────────────────────────────────────────────

def parse_questions(full_text: str, max_q: int = 180) -> dict[int, dict]:
    """
    Return {q_num: {q_text, options[4], has_image}} for all 1-max_q questions
    found in full_text.
    """
    questions: dict[int, dict] = {}
    matches = list(Q_NUM_RE.finditer(full_text))

    for idx, m in enumerate(matches):
        q_num = int(m.group(1))
        if not (1 <= q_num <= max_q):
            continue

        body_start = m.end()
        body_end = matches[idx + 1].start() if idx + 1 < len(matches) else len(full_text)
        chunk = full_text[body_start:body_end]

        # Split chunk on option labels: ['q_text', '1', opt1, '2', opt2, ...]
        parts = OPT_SPLIT_RE.split(chunk)

        q_text = normalize(parts[0])
        options = [""] * 4

        i = 1
        while i + 1 < len(parts):
            label = parts[i]
            body = parts[i + 1]
            if label.isdigit() and 1 <= int(label) <= 4:
                options[int(label) - 1] = _normalize_option(body)
            i += 2

        # Also flag has_image if any option is empty (pure structural-formula image, no text)
        has_image = bool(IMAGE_KEYWORDS_RE.search(q_text)) or any(o == "" for o in options)
        questions[q_num] = {
            "q_text": q_text,
            "options": options,
            "has_image": has_image,
        }

    # Fallback: questions that lack a period (e.g. "158 What is...") in this PDF edition
    for q_num in range(1, max_q + 1):
        if q_num in questions:
            continue
        fallback_re = re.compile(rf"(?m)^{q_num} +(?=[A-Z])")
        fm = fallback_re.search(full_text)
        if not fm:
            continue
        # Find the next question boundary for the body end
        body_start = fm.end()
        # End at next Q_NUM_RE match or next fallback number
        next_m = Q_NUM_RE.search(full_text, fm.end())
        body_end = next_m.start() if next_m else len(full_text)
        chunk = full_text[body_start:body_end]
        parts = OPT_SPLIT_RE.split(chunk)
        q_text = normalize(parts[0])
        options = [""] * 4
        i = 1
        while i + 1 < len(parts):
            label = parts[i]
            body = parts[i + 1]
            if label.isdigit() and 1 <= int(label) <= 4:
                options[int(label) - 1] = _normalize_option(body)
            i += 2
        questions[q_num] = {
            "q_text": q_text,
            "options": options,
            "has_image": bool(IMAGE_KEYWORDS_RE.search(q_text)),
        }

    return questions


# ── Answer key parser ─────────────────────────────────────────────────────────

def parse_answer_key(doc: fitz.Document, ak_page: int) -> dict[int, int]:
    """
    Parse the Que./Ans. grid table.
    Returns {q_num: correct_answer (1-4)}.
    Handles two layouts found in the PDF:
      Vertical  — "Que." alone on a line, numbers follow one-per-line, then "Ans." alone, values follow.
      Inline    — "Que. 106 107 108..." on one line, "Ans. 1 3 3..." on next line.
    Multi-correct "1,2" and bonus "B" entries: take first digit if 1-4, else skip.
    """
    lines = [
        l.strip()
        for l in doc[ak_page].get_text("text").splitlines()
        if l.strip()
    ]

    def _store(answers: dict, que_nums: list[int], ans_vals: list[str]) -> None:
        for qn, v in zip(que_nums, ans_vals):
            if re.match(r"^[1-4]", v):
                answers[qn] = int(v[0])

    answers: dict[int, int] = {}
    i = 0
    while i < len(lines):
        line = lines[i]

        # ── Hybrid format: "Que. 106" then more numbers on separate lines ──
        m_que_inline = re.match(r"^Que\.\s+(\d+)", line)
        if m_que_inline:
            que_nums = [int(x) for x in line.split()[1:] if x.isdigit()]
            j = i + 1
            # Collect remaining numbers until "Ans."
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

        # ── Vertical format: "Que." alone ───────────────────────────────────
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

        else:
            i += 1

    return answers


# ── Solution parser ───────────────────────────────────────────────────────────

def parse_solutions(doc: fitz.Document, sol_start: int, sol_end: int, max_q: int = 180) -> dict[int, str]:
    """
    Extract hint/solution text keyed by question number.
    First-occurrence-wins: chemistry sub-items (also labelled "1.", "2."…) appear
    later in the text and must not overwrite the real solutions found first.
    """
    full_text = page_text(doc, sol_start, sol_end)
    solutions: dict[int, str] = {}

    matches = list(Q_NUM_RE.finditer(full_text))
    for idx, m in enumerate(matches):
        q_num = int(m.group(1))
        if not (1 <= q_num <= max_q):
            continue
        if q_num in solutions:          # skip later duplicates (sub-items in chem solutions)
            continue
        body_start = m.end()
        body_end = matches[idx + 1].start() if idx + 1 < len(matches) else len(full_text)
        sol_text = normalize(full_text[body_start:body_end])
        if sol_text:
            solutions[q_num] = sol_text

    return solutions


# ── Image cropper ─────────────────────────────────────────────────────────────

def crop_question_image(
    doc: fitz.Document,
    q_num: int,
    year: int,
    q_start: int,
    q_end: int,
) -> Optional[str]:
    """
    Find the page that contains q_num, crop its bounding region, save as PNG.
    Returns the relative image path or None if the question wasn't located.
    """
    q_str = f"{q_num}."

    for page_idx in range(q_start, q_end):
        page = doc[page_idx]
        hits = page.search_for(q_str)
        if not hits:
            continue

        rect = hits[0]
        page_width = page.rect.width
        mid_x = page_width / 2

        # Determine which column the question is in
        in_right = rect.x0 > mid_x
        col_x0 = mid_x if in_right else 0.0
        col_x1 = page_width if in_right else mid_x

        y_start = max(rect.y0 - 4.0, 0.0)

        # Find y_end: start of the next question in the same column (look ahead ≤ 5)
        y_end = page.rect.height - 50.0
        for nq in range(q_num + 1, q_num + 6):
            next_hits = page.search_for(f"{nq}.")
            for h in next_hits:
                same_col = (h.x0 > mid_x) == in_right
                if same_col and h.y0 > y_start:
                    y_end = h.y0
                    break
            if y_end < page.rect.height - 50.0:
                break

        clip = fitz.Rect(col_x0, y_start, col_x1, y_end)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), clip=clip)

        img_path = IMAGES_DIR / f"{year}_q{q_num}.png"
        pix.save(str(img_path))
        return str(img_path)

    return None


# ── Per-year orchestration ────────────────────────────────────────────────────

def extract_year(doc: fitz.Document, year: int, config: dict) -> list[dict]:
    q_start, q_end = config["q_pages"]
    ak_page = config["ak_page"]
    sol_start, sol_end = config["sol_pages"]

    print(f"\n{'─'*50}")
    print(f"  Year: {year}  |  Q pages: {q_start+1}–{q_end}  |  AK page: {ak_page+1}")
    print(f"{'─'*50}")

    max_q = max_q_for_year(year)

    full_q_text = page_text(doc, q_start, q_end)
    questions = parse_questions(full_q_text, max_q)
    print(f"  Questions parsed : {len(questions)}")

    answers = parse_answer_key(doc, ak_page)
    print(f"  Answers parsed   : {len(answers)}")

    solutions = parse_solutions(doc, sol_start, sol_end, max_q)
    print(f"  Solutions parsed : {len(solutions)}")

    records: list[dict] = []
    missing: list[int] = []

    for q_num in range(1, max_q + 1):
        if q_num not in questions:
            missing.append(q_num)
            continue

        q = questions[q_num]
        has_image = q["has_image"]
        image_path: Optional[str] = None

        if has_image:
            image_path = crop_question_image(doc, q_num, year, q_start, q_end)

        record: dict = {
            "id": f"{year}_q{q_num}",
            "year": year,
            "q_number": q_num,
            "subject": get_subject(q_num, year),
            "text": q["q_text"],
            "options": q["options"],
            "correct_answer": answers.get(q_num),
            "solution": solutions.get(q_num, ""),
            "has_image": has_image,
            "image_path": image_path,
        }
        sub = get_sub_subject(q_num, year)
        if sub:
            record["sub_subject"] = sub
        records.append(record)

    if missing:
        print(f"  WARNING — not found: {missing}")

    img_count = sum(1 for r in records if r["has_image"])
    print(f"  Records built    : {len(records)}  (with image: {img_count})")
    return records


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    doc = fitz.open(PDF_PATH)
    all_records: list[dict] = []

    for year, config in sorted(YEAR_CONFIG.items(), reverse=True):
        records = extract_year(doc, year, config)
        all_records.extend(records)

    # ── Sample output ──
    print("\n" + "═" * 60)
    print("SAMPLE — first 5 questions")
    print("═" * 60)
    for r in all_records[:5]:
        print(json.dumps(r, indent=2, ensure_ascii=False))
        print()

    # ── Save ──
    OUTPUT_JSON.write_text(
        json.dumps(all_records, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Saved {len(all_records)} records → {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
