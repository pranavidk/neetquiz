import json

with open("public/questions.json", "r") as f:
    questions = json.load(f)

see_image_questions = []
for q in questions:
    if any(opt == "See image" for opt in q.get("options", [])):
        see_image_questions.append({
            "id": q["id"],
            "year": q.get("year"),
            "q_number": q.get("q_number"),
            "subject": q.get("subject"),
            "text": q.get("text"),
            "options": q.get("options"),
            "correct_answer": q.get("correct_answer"),
            "solution": q.get("solution")
        })

print(f"Found {len(see_image_questions)} questions with 'See image' options.")
for sq in see_image_questions[:10]:
    print(f"ID: {sq['id']}, Subject: {sq['subject']}")
    print(f"  Text: {sq['text']}")
    print(f"  Solution: {sq['solution'][:100]}...")
    print("-" * 40)

with open("see_image_questions.json", "w") as f:
    json.dump(see_image_questions, f, indent=2)
