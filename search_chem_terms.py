import json

with open("public/questions.json", "r") as f:
    questions = json.load(f)

search_terms = ["zeta potential", "synthesis gas", "carbocation", "288 pm", "dilute sulfuric acid", "Tritium is radioactive"]
for term in search_terms:
    matches = []
    for q in questions:
        # Search text, solution, options
        q_str = json.dumps(q).lower()
        if term.lower() in q_str:
            matches.append(q["id"])
    print(f"Term '{term}': matches in {matches}")
