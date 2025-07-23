import gradio as gr
from siemens_rag import ask_llm_with_rag, build_knowledge_base, load_qa_jsonl

# Load Q&A data from JSONL file (same as in siemens_rag.py)
qa_data = load_qa_jsonl("siemens_internship_qa.jsonl")
if not qa_data:
    raise RuntimeError("No data loaded from siemens_internship_qa.jsonl. Please check the file.")
kb = build_knowledge_base(qa_data)

# Build the knowledge base once

def qa_interface(question):
    answer = ask_llm_with_rag(question, kb)
    return answer

demo = gr.Interface(
    fn=qa_interface,
    inputs=gr.Textbox(lines=2, label="Ask about the Siemens internship"),
    outputs=gr.Textbox(label="Answer"),
    title="Siemens Internship Q&A LLM",
    description="Ask any question about the Siemens internship experience!"
)

demo.launch()
import json
import requests
import string

# Önce yukarıdaki RAG fonksiyonlarını kopyala...
def preprocess(text):
    text = text.lower().translate(str.maketrans('', '', string.punctuation))
    return text

def similarity(q1, q2):
    words1 = set(q1.split())
    words2 = set(q2.split())
    if not words1 or not words2:
        return 0
    return len(words1 & words2) / max(len(words1), len(words2))

qa_list = []
with open('siemens_internship_qa.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        data = json.loads(line)
        qa_list.append({
            "question": preprocess(data['prompt']),
            "raw_question": data['prompt'],
            "answer": data['completion']
        })

def ask_ollama(user_question):
    processed_q = preprocess(user_question)
    top_k = 3
    scored = []
    for qa in qa_list:
        score = similarity(processed_q, qa["question"])
        scored.append((score, qa))
    scored = sorted(scored, reverse=True, key=lambda tup: tup[0])
    top_qa = [qa for sc, qa in scored[:top_k] if sc > 0]

    knowledge = ""
    for qa in top_qa:
        knowledge += f"Question: {qa['raw_question']}\nAnswer: {qa['answer']}\n\n"
    prompt = knowledge + f"Question: {user_question}\nAnswer:"

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3",
            "prompt": prompt
        },
        stream=True
    )
    full_answer = ""
    for line in response.iter_lines():
        if line:
            part = json.loads(line)
            if "response" in part:
                full_answer += part["response"]
    return full_answer

demo = gr.Interface(
    fn=ask_ollama,
    inputs=gr.Textbox(label="Your question"),
    outputs=gr.Textbox(label="LLM's answer"),
    title="Siemens Internship QA Bot",
    description="Ask questions about my Siemens internship experience!"
)

if __name__ == "__main__":
    demo.launch()