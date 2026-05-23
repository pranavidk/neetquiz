import json

with open("see_image_questions.json", "r") as f:
    questions = json.load(f)

for i, q in enumerate(questions):
    print(f"{i+1:2d}. ID: {q['id']}, Year: {q['year']}, Q#: {q['q_number']}, Sub: {q['subject']}")
    print(f"    Text: {q['text'][:120]}...")
