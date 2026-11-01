# 📄 Resume Optimizer Agents

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![Groq](https://img.shields.io/badge/Groq-LLaMA3-orange)
![Multi-Agent](https://img.shields.io/badge/Pattern-Multi--Agent-purple)
![License](https://img.shields.io/badge/License-MIT-green)

A multi-agent AI pipeline that rewrites your resume sections (Summary, Experience, Skills) to match a target job role — using a **Writer → Critic → CEO** agent pattern powered by Groq's LLaMA 3.

---

## 🧠 How It Works

```
Your Resume (.docx)
       │
       ▼
  ✍️  Writer Agent     ← rewrites each section for the target role
       │
       ▼
  🔍  Critic Agent     ← identifies weaknesses in the rewrite
       │
       ▼
  👔  CEO Agent        ← approves or requests revision
       │
       ▼
  Improved Resume (.docx)
```

Each section (Summary, Experience, Skills) goes through up to 2 rounds of this loop before the improved version is saved.

---

## 🚀 Quickstart

### 1. Clone the repo
```bash
git clone https://github.com/<your-username>/resume-optimizer-agents.git
cd resume-optimizer-agents
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up your API key
```bash
cp .env.example .env
```
Edit `.env` and add your [Groq API key](https://console.groq.com):
```
GROQ_API_KEY=your_key_here
```

### 4. Run it
```bash
python src/resume_optimizer.py samples/resume.docx "MLOps Engineer"
```

With a job description file:
```bash
python src/resume_optimizer.py samples/resume.docx "MLOps Engineer" --jd samples/job_description.txt
```

Output is saved as `resume_improved.docx` in the same folder.

---

## 📁 Project Structure

```
resume-optimizer-agents/
├── src/
│   └── resume_optimizer.py   # main pipeline
├── samples/                  # put your resume.docx here
├── .env.example              # env variable template
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🛠️ Tech Stack

| Tool | Purpose |
|------|---------|
| [Groq](https://groq.com) | Fast LLM inference (free tier) |
| LLaMA 3.3 70B | Writer agent — high quality rewrites |
| LLaMA 3.1 8B | Critic + CEO agents — fast evaluation |
| python-docx | Parse and write `.docx` files |
| python-dotenv | Secure API key loading |

---

## 💡 Agent Pattern

This project implements the **Writer-Critic-CEO** agentic pattern:

- **Writer** — rewrites a resume section targeting the job role
- **Critic** — reviews the output and flags issues
- **CEO** — makes the final call: `APPROVED` or `REVISE`

This is a simplified version of self-reflection loops used in production LLM systems.

---

## 📌 Roadmap

- [ ] Add Langfuse observability tracing
- [ ] Support PDF input
- [ ] Add RAG to pull job description context from web
- [ ] Streamlit UI

---

## License

MIT
