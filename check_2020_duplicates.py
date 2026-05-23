import json

with open("public/questions.json", "r") as f:
    questions = json.load(f)

for q in questions:
    if q.get("year") == 2020 and q.get("q_number") in [46, 47, 48, 49, 50, 67]:
        print(f"ID: {q['id']}, Subject: {q.get('subject')}, Q#: {q.get('q_number')}")
        print(f"  Text: {q.get('text')[:100]}...")
        print(f"  Options: {q.get('options')}")
        print(f"  Correct: {q.get('correct_answer')}")
        print(f"  Solution: {q.get('solution')[:100]}...")
        print("-" * 50)
