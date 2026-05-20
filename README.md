# 🤖 AI Avatar Chatbot

An AI-powered RAG (Retrieval-Augmented Generation) chatbot that answers user queries using uploaded documents and scraped website content instead of relying solely on pretrained LLM knowledge.

---

## 📌 Overview

AI Avatar Chatbot is designed to provide accurate, context-aware responses by combining Large Language Models (LLMs) with semantic search and document retrieval techniques.

The system supports document ingestion, website scraping, vector embeddings, and intelligent response generation through a modern web interface.

---

# 🚀 Features

* 📄 PDF & document ingestion
* 🌐 Website scraping and indexing
* 🧠 Retrieval-Augmented Generation (RAG)
* 🔍 Semantic search with vector embeddings
* 🗂️ ChromaDB vector database integration
* 🤖 Qwen LLM integration
* ⚡ FastAPI backend services
* 🎨 Streamlit frontend dashboard
* 📊 Evaluation & benchmarking system
* 📈 RAG vs Qwen response comparison

---

# 🏗️ Tech Stack

| Technology             | Purpose            |
| ---------------------- | ------------------ |
| FastAPI                | Backend API        |
| Streamlit              | Frontend Dashboard |
| ChromaDB               | Vector Database    |
| HuggingFace Embeddings | Text Embeddings    |
| Qwen LLM               | Language Model     |
| SentenceTransformers   | Semantic Search    |

---

# 📂 Project Structure

```text
AI_Avatar_chatbot/
│
├── Backend/
│   ├── app/
│   ├── data/
│   ├── evaluation/
│   ├── requirements.txt
│   └── streamlit_app.py
│
└── Frontend/
```

---

# ⚙️ Installation

## 1️⃣ Clone the Repository

```bash
git clone https://github.com/Krishna-Kush-05/Ai-Avatar-Chatbot.git
cd Ai-Avatar-Chatbot/Backend
```

---

## 2️⃣ Create Virtual Environment

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

## 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

# ▶️ Running the Application

## Start Backend Server

```bash
uvicorn app.main:app --reload
```

Backend URL:

```text
http://127.0.0.1:8000
```

---

## Start Frontend

```bash
streamlit run streamlit_app.py
```

Frontend URL:

```text
http://localhost:8501
```

---

# 📄 Supported Document Formats

* PDF
* TXT
* DOCX
* Markdown (MD)

---

# 🌐 Website Ingestion

Example URL:

```text
https://mitaoe.ac.in/
```

The chatbot can scrape and index website content for semantic retrieval.

---

# 📊 Evaluation System

Run evaluation:

```bash
python evaluation/evaluator.py
```

### Metrics Used

* ✅ Answer Correctness
* ✅ Context Relevance
* ✅ Faithfulness
* ✅ Response Latency

---

# 🧠 Research Objectives

This project focuses on:

* Retrieval-Augmented Generation (RAG)
* Reducing AI hallucinations
* Domain-specific AI assistants
* Semantic retrieval systems
* Response evaluation and benchmarking

---

# 🤝 Contributors

| Name            | Role                          |
| --------------- | ----------------------------- |
| Krishna Kushwah | AI Logic, Backend Development |
| Manmath Kornule | Architecture, Team Lead       |
| Vishal Shende   | UI/UX & Frontend              |
| Pratik Mane     | DevOps & Testing              |

---

# 📜 License

This project is developed for academic and research purposes.

---

# 👨‍💻 Author

**Krishna Kushwah**

* GitHub: https://github.com/Krishna-Kush-05

---
