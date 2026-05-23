#!/usr/bin/env python3
"""
apply_transcriptions.py

Loads transcriptions.json and public/questions.json.
For each question ID in transcriptions.json, updates the matching question in questions.json with the new text and options.
Skips any entry that has a 'raw' key instead of clean text and options (these are failed transcriptions).
Saves back to public/questions.json.
Reports how many questions were updated.
"""

import os
import sys
import json

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    questions_path = os.path.join(script_dir, "public", "questions.json")
    transcriptions_path = os.path.join(script_dir, "transcriptions.json")

    # Verify file existence
    if not os.path.exists(questions_path):
        sys.exit(f"Error: {questions_path} does not exist.")

    if not os.path.exists(transcriptions_path):
        sys.exit(f"Error: {transcriptions_path} does not exist. Please run transcribe_questions.py first.")

    # Load public/questions.json
    try:
        with open(questions_path, "r", encoding="utf-8") as f:
            questions = json.load(f)
    except Exception as e:
        sys.exit(f"Error loading questions.json: {e}")

    # Load transcriptions.json
    try:
        with open(transcriptions_path, "r", encoding="utf-8") as f:
            transcriptions = json.load(f)
    except Exception as e:
        sys.exit(f"Error loading transcriptions.json: {e}")

    # Create lookup map for fast lookups
    questions_by_id = {q["id"]: q for q in questions if "id" in q}

    updated_count = 0
    skipped_raw_count = 0
    not_found_count = 0

    for q_id, transcription in transcriptions.items():
        # Skip failed transcriptions (stored as raw)
        if "raw" in transcription:
            skipped_raw_count += 1
            continue

        if q_id not in questions_by_id:
            print(f"[WARNING] Question ID {q_id} from transcriptions.json was not found in questions.json.")
            not_found_count += 1
            continue

        new_text = transcription.get("text")
        new_options = transcription.get("options")

        if not new_text or not new_options:
            print(f"[WARNING] Question ID {q_id} has invalid/empty text or options in transcriptions.json. Skipping.")
            continue

        # Apply updates
        questions_by_id[q_id]["text"] = new_text
        questions_by_id[q_id]["options"] = new_options
        updated_count += 1

    # Save the updated questions list back to questions.json
    if updated_count > 0:
        try:
            with open(questions_path, "w", encoding="utf-8") as f:
                json.dump(questions, f, indent=2, ensure_ascii=False)
            print(f"\nSuccessfully updated {updated_count} questions in questions.json.")
        except Exception as e:
            sys.exit(f"Error saving questions.json: {e}")
    else:
        print("\nNo questions were updated.")

    print("\n── APPLICATION SUMMARY ──────────")
    print(f"Total transcription entries : {len(transcriptions)}")
    print(f"Successfully updated        : {updated_count}")
    print(f"Skipped failed (raw)        : {skipped_raw_count}")
    if not_found_count > 0:
        print(f"Not found in questions.json : {not_found_count}")

if __name__ == "__main__":
    main()
