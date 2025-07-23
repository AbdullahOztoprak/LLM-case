## Siemens Internship Q&A LLM

An interactive Q&A system for Siemens internship experience, powered by Retrieval-Augmented Generation (RAG) and Large Language Models (LLM).

---

### 🚀 Features
- Ask any question about the Siemens internship
- Uses your own Q&A dataset for accurate, context-aware answers
- Gradio web interface for easy interaction

---

### 📦 Requirements
- Python 3.8+
- [Ollama](https://ollama.com/) (for local LLM inference)
- gradio, requests, numpy (see `requirements.txt`)

---

### ⚡️ Quick Start
1. Clone this repo:
   ```bash
   git clone https://code.siemens.com/abdullah.oztoprak/llm-case.git
   cd llm-case
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Start the Ollama server:
   ```bash
   ollama serve
   ```
4. Pull the required models:
   ```bash
   ollama pull llama3
   ollama pull nomic-embed-text
   ```
   (These are the default LLM and embedding models used in this project. You can change them in the code if needed.)
5. Run the app:
   ```bash
   python qa_gradio_app.py
   ```
6. Open the Gradio link in your browser and start asking questions!

---

### 📁 Data
- All Q&A pairs are in `siemens_internship_qa.jsonl` (editable, extendable)

---

### 🤝 Contributing
Pull requests and suggestions are welcome!

---

### © 2025 Abdullah Oztoprak
