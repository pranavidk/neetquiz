#!/usr/bin/env python3
"""
transcribe_questions.py

Uses the OpenAI API with GPT-4o-mini vision to transcribe NEET question images.
Resumes from an interrupted state using transcriptions.json or transcriptions_test.json.

Run:
    python3 transcribe_questions.py [--test]
"""

import os
import sys
import json
import time
import base64
import argparse
import datetime
from openai import OpenAI

# Pricing constants for gpt-4o-mini
COST_PER_1M_INPUT = 0.15   # $0.15 per 1M tokens
COST_PER_1M_OUTPUT = 0.60  # $0.60 per 1M tokens

def parse_arguments():
    parser = argparse.ArgumentParser(description="Transcribe NEET questions using OpenAI GPT-4o-mini Vision")
    parser.add_argument("--test", action="store_true", help="Run on only 5 test questions (one of each type)")
    return parser.parse_args()

def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def select_test_questions(matched_questions):
    """
    Pick one Physics, one Chemistry, one Biology, one match-the-column, and one empty-options question automatically.
    Ensures all 5 selected questions are distinct.
    """
    selected = []
    selected_ids = set()

    # 1. Find one empty-options question
    for q in matched_questions:
        if any(opt == "" for opt in q.get("options", [])):
            selected.append(q)
            selected_ids.add(q["id"])
            break

    # 2. Find one match-the-column question
    for q in matched_questions:
        if q["id"] in selected_ids:
            continue
        text = q.get("text", "").lower()
        if "match" in text and "column" in text:
            selected.append(q)
            selected_ids.add(q["id"])
            break

    # 3. Find one Physics question
    for q in matched_questions:
        if q["id"] in selected_ids:
            continue
        if q.get("subject") == "Physics":
            selected.append(q)
            selected_ids.add(q["id"])
            break

    # 4. Find one Chemistry question
    for q in matched_questions:
        if q["id"] in selected_ids:
            continue
        if q.get("subject") == "Chemistry":
            selected.append(q)
            selected_ids.add(q["id"])
            break

    # 5. Find one Biology question
    for q in matched_questions:
        if q["id"] in selected_ids:
            continue
        if q.get("subject") == "Biology":
            selected.append(q)
            selected_ids.add(q["id"])
            break

    return selected

def main():
    args = parse_arguments()

    # 1. Verify OPENAI_API_KEY environment variable is set
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable is not set.", file=sys.stderr)
        print("Please export OPENAI_API_KEY before running this script.", file=sys.stderr)
        sys.exit(1)

    client = OpenAI(api_key=api_key)

    # 2. Define file paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    questions_path = os.path.join(script_dir, "public", "questions.json")
    images_dir = os.path.join(script_dir, "public", "images")
    
    output_filename = "transcriptions_test.json" if args.test else "transcriptions.json"
    output_path = os.path.join(script_dir, output_filename)

    # 3. Load public/questions.json
    if not os.path.exists(questions_path):
        print(f"Error: {questions_path} does not exist.", file=sys.stderr)
        sys.exit(1)

    try:
        with open(questions_path, "r", encoding="utf-8") as f:
            questions = json.load(f)
    except Exception as e:
        print(f"Error loading questions.json: {e}", file=sys.stderr)
        sys.exit(1)

    # 4. Load existing transcriptions if file exists (for resuming)
    transcriptions = {}
    if os.path.exists(output_path):
        try:
            with open(output_path, "r", encoding="utf-8") as f:
                transcriptions = json.load(f)
            print(f"Loaded {len(transcriptions)} existing transcriptions from {output_filename}")
        except Exception as e:
            print(f"Warning: Failed to load existing transcriptions from {output_filename}: {e}", file=sys.stderr)

    # 5. Filter questions to find those that match transcription criteria:
    #    - has_image: true AND the PNG exists in public/images/
    #    - OR any option is an empty string
    matched_questions = []
    for q in questions:
        q_id = q.get("id")
        has_img = q.get("has_image", False)
        img_path = q.get("image_path")
        
        # Check image existence
        img_exists = False
        local_img_path = None
        if img_path:
            local_img_path = os.path.join(script_dir, "public", img_path)
            img_exists = os.path.exists(local_img_path)
        else:
            # Fallback check for id.png in public/images/
            fallback_img_path = os.path.join(images_dir, f"{q_id}.png")
            if os.path.exists(fallback_img_path):
                local_img_path = fallback_img_path
                img_exists = True

        has_empty_opt = any(opt == "" for opt in q.get("options", []))

        if (has_img and img_exists) or has_empty_opt:
            # Keep a reference to the verified local image path if any
            q["_local_image_path"] = local_img_path if img_exists else None
            matched_questions.append(q)

    # If test mode, select 5 test questions, otherwise process all matched
    if args.test:
        questions_to_process = select_test_questions(matched_questions)
        print(f"Test mode: selected {len(questions_to_process)} distinct questions covering 5 types.")
    else:
        questions_to_process = matched_questions
        print(f"Found {len(questions_to_process)} questions matching transcription criteria.")

    total_to_process = len(questions_to_process)
    successful = 0
    failed = 0
    skipped = 0
    total_prompt_tokens = 0
    total_completion_tokens = 0

    system_prompt = (
        "You are an expert at transcribing Indian NEET exam questions.\n"
        "Extract the question text and all 4 options exactly as shown.\n"
        "Use LaTeX for all math: $...$ inline, $$...$$ for display math.\n"
        "Use proper unicode for Greek letters: α β γ δ θ λ μ π σ ω.\n"
        "For chemistry write molecular formulas normally: H2O, CO2.\n"
        "For match-the-column questions preserve the table structure using line breaks.\n"
        "Return ONLY valid JSON with no markdown, no explanation."
    )

    # 6. Process each question
    for idx, q in enumerate(questions_to_process, 1):
        q_id = q["id"]

        # Skip if already done and successfully parsed
        if q_id in transcriptions and "raw" not in transcriptions[q_id]:
            print(f"[SKIP] {q_id} — already done")
            skipped += 1
            continue

        local_img_path = q.get("_local_image_path")
        q_text = q.get("text", "")
        q_options = q.get("options", [])
        q_solution = q.get("solution", "")

        # Prepare user prompt and message content
        if local_img_path:
            # Vision prompt
            user_prompt = (
                "Extract the question and all 4 options from this NEET exam image.\n"
                "Return as JSON exactly like this:\n"
                "{\n"
                '  "text": "full question text here",\n'
                '  "options": ["option 1 text", "option 2 text", "option 3 text", "option 4 text"]\n'
                "}\n"
                "Do not include option numbers like (1)(2)(3)(4) in the option text.\n"
                "If math is present use LaTeX notation.\n"
                'If an option is a pure diagram or graph with no text write "See image".\n'
                "For match-the-column questions format the table with line breaks so it is readable.\n\n"
                "CRITICAL INSTRUCTIONS:\n"
                "1. The question 'text' must contain the full question text including any statements "
                "(e.g., A, B, C, D, E, F...) or tables that lead up to the final options.\n"
                "2. The 'options' array must contain the 4 final multiple-choice selections "
                "(typically labeled (1), (2), (3), (4) at the bottom). Do not use the statements/conditions "
                "as options."
            )
            
            try:
                base64_image = encode_image_to_base64(local_img_path)
            except Exception as e:
                print(f"[{idx}/{total_to_process}] {q_id} — failed encoding image: {e}")
                failed += 1
                continue

            user_content = [
                {
                    "type": "text",
                    "text": user_prompt
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64_image}",
                        "detail": "high"
                    }
                }
            ]
        else:
            # Text prompt fallback (no image file)
            user_prompt = (
                "Extract and clean the question and all 4 options from this NEET exam question text. "
                "Ensure any missing or malformed options are reconstructed or corrected based on context and/or the solution.\n"
                f"Question Text: {q_text}\n"
                f"Options: {q_options}\n"
                f"Solution (if any): {q_solution}\n\n"
                "Return as JSON exactly like this:\n"
                "{\n"
                '  "text": "full question text here",\n'
                '  "options": ["option 1 text", "option 2 text", "option 3 text", "option 4 text"]\n'
                "}\n"
                "Do not include option numbers like (1)(2)(3)(4) in the option text.\n"
                "If math is present use LaTeX notation.\n"
                "For match-the-column questions format the table with line breaks so it is readable."
            )
            user_content = [
                {
                    "type": "text",
                    "text": user_prompt
                }
            ]

        # Call the OpenAI API with retry logic for 429/Rate Limits
        response = None
        max_retries = 5
        base_delay = 2.0  # seconds
        try:
            for attempt in range(1, max_retries + 1):
                try:
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_content}
                        ],
                        max_tokens=1000,
                        temperature=0.0,
                        response_format={"type": "json_object"}
                    )
                    break  # Success
                except Exception as api_err:
                    error_str = str(api_err).lower()
                    is_retryable = any(code in error_str for code in ["429", "rate_limit", "rate limit", "500", "502", "503", "504"])
                    if is_retryable and attempt < max_retries:
                        sleep_time = base_delay * (2 ** (attempt - 1))
                        print(f"[{idx}/{total_to_process}] {q_id} — Retryable error ({type(api_err).__name__}). Retrying in {sleep_time:.1f}s (Attempt {attempt}/{max_retries})...")
                        time.sleep(sleep_time)
                    else:
                        raise api_err
            
            # Keep track of usage tokens if available
            tokens_used = 0
            if response.usage:
                total_prompt_tokens += response.usage.prompt_tokens
                total_completion_tokens += response.usage.completion_tokens
                tokens_used = response.usage.total_tokens

            # Parse content
            content = response.choices[0].message.content
            timestamp_str = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

            try:
                parsed_json = json.loads(content)
                text = parsed_json.get("text", "")
                options = parsed_json.get("options", [])
                
                # Verify options length, make sure it is exactly 4 elements
                if not isinstance(options, list) or len(options) != 4:
                    # Pad or trim to 4 options
                    if not isinstance(options, list):
                        options = []
                    while len(options) < 4:
                        options.append("")
                    options = options[:4]

                # Update transcriptions dict
                transcriptions[q_id] = {
                    "text": text,
                    "options": options,
                    "model": "gpt-4o-mini",
                    "timestamp": timestamp_str
                }
                successful += 1
                print(f"[{idx}/{total_to_process}] {q_id} — done (tokens: {tokens_used})")

            except json.JSONDecodeError:
                # If JSON parsing fails, save raw response under raw key
                transcriptions[q_id] = {
                    "raw": content,
                    "model": "gpt-4o-mini",
                    "timestamp": timestamp_str
                }
                failed += 1
                print(f"[{idx}/{total_to_process}] {q_id} — failed JSON parsing (tokens: {tokens_used})")

            # Write updated transcriptions to file immediately to avoid data loss
            with open(output_path, "w", encoding="utf-8") as out_f:
                json.dump(transcriptions, out_f, indent=2, ensure_ascii=False)

        except Exception as e:
            failed += 1
            print(f"[{idx}/{total_to_process}] {q_id} — API call failed: {e}")

        # Respect request delay
        time.sleep(0.5)

    # 7. Print final summary
    cost = (total_prompt_tokens * COST_PER_1M_INPUT / 1_000_000) + (total_completion_tokens * COST_PER_1M_OUTPUT / 1_000_000)

    print("\n── TRANSCRIPTION SUMMARY ──────────")
    print(f"Total processed  : {successful + failed}")
    print(f"Successful       : {successful}")
    print(f"Failed           : {failed}")
    print(f"Skipped          : {skipped}")
    print(f"Estimated cost   : ${cost:.4f}")
    print(f"Saved to         : {output_filename}")

if __name__ == "__main__":
    main()
