import json
import requests

# --- Kendi QA verilerini oku ---
knowledge = ""
with open('siemens_internship_qa.jsonl', 'r', encoding='utf-8') as f:
    for idx, line in enumerate(f):
        if idx > 4:
            break
        data = json.loads(line)
        question = data['prompt']
        answer = data['completion']
        knowledge += f"Question: {question}\nAnswer: {answer}\n\n"

user_question = "Which tools did you use during your internship?"
prompt = knowledge + f"Question: {user_question}\nAnswer:"

# --- Ollama API'ya istek gönder (stream=True) ---
response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "llama3",
        "prompt": prompt
    },
    stream=True   # Streaming cevabı parça parça dön!
)

# Streaming cevap parçalarını birleştir
full_answer = ""
for line in response.iter_lines():
    if line:
        part = json.loads(line)
        if "response" in part:
            full_answer += part["response"]

print(full_answer)