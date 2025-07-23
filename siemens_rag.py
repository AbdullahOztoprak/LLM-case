import ollama
import requests
import json
import numpy as np
import os

# Load all Q&A pairs from siemens_internship_qa.jsonl
def load_qa_jsonl(jsonl_path):
    data = []
    if not os.path.exists(jsonl_path):
        print(f"[ERROR] File not found: {jsonl_path}")
        return data
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    data.append(json.loads(line))
                except Exception as e:
                    print(f"[ERROR] Could not parse line: {line}\n{e}")
    return data

# Example internship data (you can expand this list as needed)
    # ... rest of your data
    # Removed hardcoded internship_data list

# Make sure you have an embedding model pulled, e.g., `ollama pull nomic-embed-text`
EMBEDDING_MODEL = "nomic-embed-text"
LLM_MODEL = "llama3" # Or your preferred Llama 3 variant



def get_embedding(text):
    """
    Generates an embedding for the given text using Ollama HTTP API.
    Returns a numpy array of the embedding.
    """
    url = "http://localhost:11434/api/embeddings"
    payload = {
        "model": EMBEDDING_MODEL,
        "prompt": text
    }
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return np.array(response.json()['embedding'])

def cosine_similarity(vec1, vec2):
    """
    Calculates cosine similarity between two vectors.
    """
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

def build_knowledge_base(data):
    """
    Builds an in-memory knowledge base with embeddings for each document.
    """
    knowledge_base = []
    print(f"Generating embeddings for {len(data)} documents...")
    for item in data:
        # Use both prompt and completion for embedding to improve direct Q&A retrieval
        combined_text = item["prompt"] + " " + item["completion"]
        embedding = get_embedding(combined_text)
        knowledge_base.append({"text": item["completion"], "embedding": embedding, "prompt": item["prompt"]})
    print("Embeddings generated.")
    return knowledge_base

def retrieve_context(query, knowledge_base, top_k=3):
    """
    Retrieves the most relevant context from the knowledge base for a given query.
    Returns a string containing the top_k most similar texts.
    """
    # First, check for exact prompt match (case-insensitive, stripped)
    for doc in knowledge_base:
        if doc["prompt"].strip().lower() == query.strip().lower():
            return doc["completion"]

    # If no exact match, use embedding similarity as before
    query_embedding = get_embedding(query)
    similarities = []
    for doc in knowledge_base:
        similarity = cosine_similarity(query_embedding, doc["embedding"])
        similarities.append((similarity, doc["text"], doc["prompt"]))
    similarities.sort(key=lambda x: x[0], reverse=True)
    # Lower top_k to 1 for more focused context
    context = [text for sim, text, prompt in similarities[:1]]
    return "\n\n".join(context)

def ask_llm_with_rag(query, knowledge_base, llm_model=LLM_MODEL):
    """
    Asks the LLM a question, augmented with retrieved context.
    Returns the LLM's answer as a string.
    """
    context = retrieve_context(query, knowledge_base)

    # Simplified prompt for better LLM focus
    augmented_prompt = f"Context:\n{context}\n\nQuestion: {query}\nAnswer:"

    print("\n--- Sending Augmented Prompt to LLM ---")
    print(augmented_prompt)  # For debugging/understanding what's sent

    url = "http://localhost:11434/api/chat"
    payload = {
        "model": llm_model,
        "messages": [
            {"role": "user", "content": augmented_prompt}
        ]
    }
    try:
        response = requests.post(url, json=payload, stream=True, timeout=60)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Ollama API error: {e}")
        return "Could not reach Ollama API. Please make sure the Ollama server is running."

    full_content = ""
    try:
        for line in response.iter_lines():
            if line:
                print("[DEBUG] Ollama response line:", line)
                try:
                    data = json.loads(line)
                except Exception as e:
                    print(f"[ERROR] JSON decode error: {e}")
                    continue
                if "message" in data and "content" in data["message"]:
                    full_content += data["message"]["content"]
                    print("[DEBUG] Current content:", full_content)
    except Exception as e:
        print(f"[ERROR] Streaming response error: {e}")
        return "An error occurred while receiving the model's response."

    if not full_content.strip():
        full_content = "No answer received from the model or no relevant information in the context."
    return full_content

# --- Main execution ---
if __name__ == "__main__":
    # 1. Load all Q&A pairs from JSONL file
    qa_data = load_qa_jsonl("siemens_internship_qa.jsonl")
    if not qa_data:
        print("[ERROR] No data loaded from siemens_internship_qa.jsonl. Exiting.")
        exit(1)
    kb = build_knowledge_base(qa_data)

    # 2. Interactive question-answer loop
    while True:
        user_query = input("\nAsk me about the Siemens internship (or type 'exit' to quit): ")
        if user_query.lower() == 'exit':
            break

        answer = ask_llm_with_rag(user_query, kb)
        print("\n--- LLM's Answer ---")
        print(answer)
        print("--------------------")