#!/usr/bin/env python3
"""
fix_garbled_math.py

Uses GPT-4o-mini to reconstruct garbled mathematical expressions in questions
where PDF extraction destroyed the structure of fractions, subscripts, and
chemical formulas.

Sends the garbled text + options + solution to GPT and asks it to reconstruct
the correct mathematical expressions.
"""
import os
import sys
import json
import time
import re
from openai import OpenAI

# List of question IDs with garbled math structure
GARBLED_IDS = [
    '2025_q15', '2024_q59', '2023_q16', '2023_q98', '2022_q34',
    '2021_q30', '2021_q50', '2020_q23', '2019_q89', '2018_q23',
    '2017_q5', '2017_q16', '2017_q37', '2016_q2', '2016_q10',
    'mock1_q20', 'mock1_q38', 'mock1_q45', 'mock1_q46', 'mock1_q55',
    'mock2_q3', 'mock2_q4', 'mock2_q19',
    'mock3_q26', 'mock3_q29', 'mock3_q32', 'mock3_q82', 'mock3_q83',
    'mock4_q4', 'mock4_q89',
    'mock5_q8',
    'mock6_q10', 'mock6_q37',
    'mock7_q29', 'mock7_q30',
    'mock8_q1', 'mock8_q6', 'mock8_q17', 'mock8_q18', 'mock8_q40', 'mock8_q69',
    'mock9_q41', 'mock9_q68',
    # Also include the rope/friction question from screenshot
    '2017_q27',
]


def main():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not set.", file=sys.stderr)
        sys.exit(1)

    client = OpenAI(api_key=api_key)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    questions_path = os.path.join(script_dir, "public", "questions.json")
    output_path = os.path.join(script_dir, "math_fixes.json")

    with open(questions_path, "r", encoding="utf-8") as f:
        questions = json.load(f)

    questions_by_id = {q["id"]: q for q in questions}

    # Load existing fixes if resuming
    fixes = {}
    if os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8") as f:
            fixes = json.load(f)
        print(f"Loaded {len(fixes)} existing fixes from math_fixes.json")

    system_prompt = (
        "You are an expert at NEET exam physics and chemistry questions.\n"
        "I will give you a question where the text and/or options were garbled by bad PDF extraction.\n"
        "The PDF extractor flattened fractions, subscripts, and superscripts into a jumbled sequence.\n"
        "For example:\n"
        "  '2 1 2 1 (L + L )' should be 'L₂/(L₁ + L₂)'\n"
        "  '5(g) 3(g) 2(g) PCl PCl Cl + °' should be 'PCl₅(g) ⇌ PCl₃(g) + Cl₂(g)'\n"
        "  '22 2 7.8 10 amp m × ×' should be '7.8 × 10²² amp·m²'\n"
        "  '1 μ' could be 'λ/μ' or '1/μ'\n\n"
        "Use the SOLUTION text (which often has the correct answer) to figure out what the options should be.\n"
        "Return ONLY valid JSON with this exact structure:\n"
        '{"text": "corrected question text", "options": ["opt1", "opt2", "opt3", "opt4"]}\n\n'
        "Rules:\n"
        "- If the question text is already readable, keep it as-is\n"
        "- Fix ALL 4 options to be readable and correct\n"
        "- Use Unicode symbols: ×, ², ³, ⁻¹, ₁, ₂, ₃, ⇌, →, °, λ, μ, θ, π, ω, ρ, α, β, φ, Δ, Ω, ε, σ, τ, γ\n"
        "- For fractions use a/b notation (e.g. L₂/L₁)\n"
        "- For chemistry: PCl₅(g) ⇌ PCl₃(g) + Cl₂(g)\n"
        "- Do NOT use LaTeX $...$ notation, use plain Unicode\n"
        "- Do NOT include option labels like (1)(2)(3)(4) or (A)(B)(C)(D)\n"
    )

    total = len(GARBLED_IDS)
    successful = 0
    failed = 0
    skipped = 0

    for idx, q_id in enumerate(GARBLED_IDS, 1):
        if q_id in fixes and "raw" not in fixes[q_id]:
            print(f"[SKIP] {q_id} — already fixed")
            skipped += 1
            continue

        if q_id not in questions_by_id:
            print(f"[SKIP] {q_id} — not found in questions.json")
            skipped += 1
            continue

        q = questions_by_id[q_id]
        user_prompt = (
            f"Subject: {q.get('subject', 'Unknown')}\n"
            f"Question text: {q.get('text', '')}\n"
            f"Option 1: {q['options'][0] if len(q['options']) > 0 else ''}\n"
            f"Option 2: {q['options'][1] if len(q['options']) > 1 else ''}\n"
            f"Option 3: {q['options'][2] if len(q['options']) > 2 else ''}\n"
            f"Option 4: {q['options'][3] if len(q['options']) > 3 else ''}\n"
            f"Correct answer: Option {q.get('correct_answer', '?')}\n"
            f"Solution: {q.get('solution', 'N/A')}\n\n"
            "Please reconstruct the correct question text and all 4 options."
        )

        max_retries = 5
        base_delay = 2.0
        response = None

        try:
            for attempt in range(1, max_retries + 1):
                try:
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        max_tokens=800,
                        temperature=0.0,
                        response_format={"type": "json_object"}
                    )
                    break
                except Exception as api_err:
                    error_str = str(api_err).lower()
                    is_retryable = any(code in error_str for code in ["429", "rate_limit", "rate limit", "500", "502", "503", "504"])
                    if is_retryable and attempt < max_retries:
                        sleep_time = base_delay * (2 ** (attempt - 1))
                        print(f"[{idx}/{total}] {q_id} — Retrying in {sleep_time:.1f}s (Attempt {attempt}/{max_retries})...")
                        time.sleep(sleep_time)
                    else:
                        raise api_err

            content = response.choices[0].message.content

            try:
                parsed = json.loads(content)
                new_text = parsed.get("text", "")
                new_opts = parsed.get("options", [])

                if not isinstance(new_opts, list) or len(new_opts) != 4:
                    raise ValueError(f"Expected 4 options, got {len(new_opts) if isinstance(new_opts, list) else 'non-list'}")

                fixes[q_id] = {
                    "text": new_text,
                    "options": new_opts,
                    "model": "gpt-4o-mini",
                    "original_text": q.get("text", ""),
                    "original_options": q.get("options", []),
                }
                successful += 1
                print(f"[{idx}/{total}] {q_id} — fixed")

            except (json.JSONDecodeError, ValueError) as e:
                fixes[q_id] = {"raw": content, "error": str(e)}
                failed += 1
                print(f"[{idx}/{total}] {q_id} — parse error: {e}")

            # Save after each question
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(fixes, f, indent=2, ensure_ascii=False)

        except Exception as e:
            failed += 1
            print(f"[{idx}/{total}] {q_id} — API error: {e}")

        time.sleep(0.3)

    print(f"\n── MATH FIX SUMMARY ──────────")
    print(f"Total         : {total}")
    print(f"Successful    : {successful}")
    print(f"Failed        : {failed}")
    print(f"Skipped       : {skipped}")
    print(f"Saved to      : math_fixes.json")

    # Now apply fixes to questions.json
    if successful > 0:
        applied = 0
        for q_id, fix in fixes.items():
            if "raw" in fix:
                continue
            if q_id in questions_by_id:
                questions_by_id[q_id]["text"] = fix["text"]
                questions_by_id[q_id]["options"] = fix["options"]
                applied += 1

        with open(questions_path, "w", encoding="utf-8") as f:
            json.dump(questions, f, indent=2, ensure_ascii=False)
        print(f"Applied {applied} fixes to questions.json")


if __name__ == "__main__":
    main()
