import requests
import json

# Tüm QA verilerini oku (ilk 5 tanesini örnek olarak prompt'a ekle)
veri = []
with open('siemens_internship_qa.jsonl', encoding='utf-8') as f:
    for idx, line in enumerate(f):
        if idx > 4: break
        data = json.loads(line)
        veri.append(f"Soru: {data['prompt']}\nCevap: {data['completion']}")

knowledge = "\n".join(veri)
user_question = "Stajda şube güvenliği için ne yaptın?"
prompt = knowledge + f"\nSoru: {user_question}\nCevap:"

response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "llama3",
        "prompt": prompt
    }
)
print(response.json()["response"])