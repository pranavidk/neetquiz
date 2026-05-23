import json

with open("public/questions.json", "r") as f:
    questions = json.load(f)

for q in questions:
    if q["id"].startswith("2020_q") and 45 <= q["q_number"] <= 55:
        print(f"ID: {q['id']}, Year: {q['year']}, Q#: {q['q_number']}, Sub: {q['subject']}")
        print(f"  Text: {q.get('text')}")
        print(f"  Options: {q.get('options')}")
        print(f"  Correct: {q.get('correct_answer')}")
        print(f"  Solution: {q.get('solution')}")
        print(f"  Has Image: {q.get('has_image')}")
        print(f"  Image Path: {q.get('image_path')}")
        print("-" * 50)
