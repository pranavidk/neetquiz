import json

with open("public/questions.json", "r") as f:
    questions = json.load(f)

q_2020 = [q for q in questions if q.get("year") == 2020]
print(f"Total 2020 questions: {len(q_2020)}")
subjects = {}
for q in q_2020:
    sub = q.get("subject")
    subjects[sub] = subjects.get(sub, 0) + 1

print("Subjects in 2020:", subjects)

for idx, q in enumerate(q_2020[:60]):
    print(f"{idx+1:2d}. ID: {q['id']}, Subject: {q.get('subject')}, Q#: {q.get('q_number')}, Text: {q.get('text')[:60]}...")
