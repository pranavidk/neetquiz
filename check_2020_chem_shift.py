import json

with open("public/questions.json", "r") as f:
    questions = json.load(f)

q_2020_chem = [q for q in questions if q.get("year") == 2020 and q.get("subject") == "Chemistry"]
q_2020_chem.sort(key=lambda x: x["q_number"])

for q in q_2020_chem:
    print(f"Q#: {q['q_number']}, ID: {q['id']}")
    print(f"  Text: {q.get('text')[:80]}...")
    print(f"  Options: {q.get('options')}")
    print(f"  Solution: {q.get('solution')[:80]}...")
    print("-" * 50)
