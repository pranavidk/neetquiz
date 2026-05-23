#!/usr/bin/env python3
"""
fix_pdf_junk.py

Cleans up PDF extraction artifacts from public/questions.json:
1. Removes "SKC SIR" / "SKC" author watermarks from options and text
2. Removes trailing "E XX" page/question numbers from options
3. Removes leaked section headers like "Chemistry : Section-A (Q. No. 051 to 085)"
"""
import json
import os
import re
import sys

def clean_skc(s):
    """Remove SKC SIR watermark and variants."""
    if not s:
        return s
    # Remove "SKC SIR" and "SKC" at word boundaries (with optional surrounding whitespace)
    s = re.sub(r'\s*SKC\s+SIR\s*', '', s)
    s = re.sub(r'\s*SKCC?\s*$', '', s)  # trailing SKC/SKCC
    return s.strip()


def clean_page_numbers(s):
    """Remove trailing 'E XX' page numbers from PDF extraction."""
    if not s:
        return s
    # Remove trailing patterns like "E 42", "E 71", " E 82" at end of string
    s = re.sub(r'\s+E\s+\d{2,3}\s*$', '', s)
    return s.strip()


def clean_section_headers(s):
    """Remove leaked section headers like 'Chemistry : Section-A (Q. No. 051 to 085)'."""
    if not s:
        return s
    s = re.sub(
        r'\s*(Physics|Chemistry|Biology)\s*:\s*Section-?[A-Z]\s*\(Q\.?\s*No\.?\s*\d+\s*to\s*\d+\)\s*',
        '', s
    )
    return s.strip()


def clean_string(s):
    """Apply all cleanups to a string."""
    s = clean_skc(s)
    s = clean_page_numbers(s)
    s = clean_section_headers(s)
    return s


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    questions_path = os.path.join(script_dir, "public", "questions.json")

    with open(questions_path, "r", encoding="utf-8") as f:
        questions = json.load(f)

    fixed_count = 0
    skc_fixed = 0
    page_num_fixed = 0
    section_fixed = 0

    for q in questions:
        changed = False

        # Fix text
        old_text = q.get("text", "")
        new_text = clean_string(old_text)
        if new_text != old_text:
            q["text"] = new_text
            changed = True
            if 'SKC' in old_text: skc_fixed += 1
            if re.search(r'\s+E\s+\d{2,3}\s*$', old_text): page_num_fixed += 1

        # Fix options
        old_opts = q.get("options", [])
        new_opts = [clean_string(opt) for opt in old_opts]
        if new_opts != old_opts:
            q["options"] = new_opts
            changed = True
            for old_o, new_o in zip(old_opts, new_opts):
                if old_o != new_o:
                    if 'SKC' in old_o: skc_fixed += 1
                    if re.search(r'\s+E\s+\d{2,3}\s*$', old_o): page_num_fixed += 1
                    if re.search(r'Section-?[A-Z]', old_o): section_fixed += 1

        if changed:
            fixed_count += 1

    # Save
    with open(questions_path, "w", encoding="utf-8") as f:
        json.dump(questions, f, indent=2, ensure_ascii=False)

    print(f"\n── PDF JUNK CLEANUP SUMMARY ──────────")
    print(f"Questions fixed       : {fixed_count}")
    print(f"SKC watermarks removed: {skc_fixed}")
    print(f"Page numbers removed  : {page_num_fixed}")
    print(f"Section headers removed: {section_fixed}")
    print(f"Saved to              : {questions_path}")


if __name__ == "__main__":
    main()
