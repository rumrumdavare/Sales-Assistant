<div align="center">

## 📇 AI Sales Assistant — Pre-Call Brief Generator

An AI-powered assistant that creates concise, data-backed pre-call briefs for sales and account managers.
Built with a ReAct agent, SQL tools, vector-search notes, and a polished Streamlit interface.

---
#### Built with

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white) ![LangChain](https://img.shields.io/badge/LangChain-4585F3?style=for-the-badge&logo=chainlink&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-FF76A8?style=for-the-badge&logo=groq&logoColor=white) ![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)

</div>

---

### 🌟 Overview

The assistant generates two types of outputs:

📝 **Full Brief** — Overview, KPIs, Risks, References, and synthesized insights

💬 **Talking Points Only** — 3–5 actionable, call-ready bullets

Both powered by a *LangChain ReAct* agent orchestrating *SQL + RAG* tools intelligently.

### 🧰 Tech Stack

1. **Frontend**: Streamlit
2. **Backend**: Python 3.11, LangChain
3. **LLM**: Groq (Llama-3.x-Instant)
4. **Database**: SQLite
5. **Vectorstore**: Chroma + MiniLM
6. **Agent**: ReAct reasoning with tools

### 📁 Project Structure
```
sales assistant/
│
├── ai_sales_assistant/
│   ├── agent/
│   ├── app/
│   ├── db/
│   ├── rag/
│   └── __init__.py
│
├── data/
│   ├── raw/
│   ├── meeting_notes/
│   └── vectorstore/
│
├── db/
│   └── schema.sql
│
├── scripts/
│   ├── build_vectorstore.py
│   ├── seed_data.py
│   ├── init_db.py
│   ├── demo_generate_data.py
│
├── local.db
├── .env
├── requirements.txt
└── README.md
```

### ⚙️ Installation

```bash
git clone <your-repo-url>
cd <project-folder>

python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

### 🔑 Environment Variables

Create .env:
```ini
GROQ_API_KEY=your_key
GROQ_MODEL=llama-3.1-8b-instant
```
(Streamlit Cloud → add to Secrets Manager)

### 🚀 Running the App

```bash
streamlit run ai_sales_assistant/app/streamlit_app.py
```
Then choose:
- a client name,
- a brief type (full or talking points),
- and click Generate Brief.

### 🧠 How It Works

1. ReAct Agent Logic
The agent follows a deterministic workflow:
- Resolve client via SQL
- Retrieve KPIs
- Pull latest interactions
- Fetch open tickets
- Perform notes search via vectorstore
- Synthesize a clean, structured brief

2. Retrieval-Augmented Notes
```
Notes → embedded using MiniLM
Stored in Chroma
Filtered & summarized per client
```

3. Streamlit UI
- Selectboxes for client & brief type
- Clean Markdown output
- Session-based usage limits

### 🛣️ Roadmap

- PDF export for briefs
- KPI charts (trend lines)
- OCR ingestion: scan handwritten notes or photos from notebooks → process & embed into the vectorstore as additional meeting notes.
- Multi-agent pipeline (validator + writer)
- User authentication

### 📄 License

Distributed under the **MIT License**.
See ![```LICENSE```](https://github.com/rumrumdavare/Sales-Assistant/blob/changes/LICENSE) for details.