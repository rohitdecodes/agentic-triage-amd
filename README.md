---
title: AgentTriage AMD Developer Cloud
emoji: 🔴
colorFrom: red
colorTo: blue
sdk: docker
pinned: false
---

# 🔴 AgentTriage — Agentic SRE Incident Response on AMD Developer Cloud

> Multi-agent log triage system that autonomously diagnoses production incidents using AMD-hosted LLMs and a LangGraph-powered agent pipeline.

Built for the **AMD Developer Cloud Hackathon — Track 1: AI Agents & Agentic Workflows**

👉 **[Try the Live Demo](https://OGrohit-agentic-triage-amd.hf.space)**

---

## 📌 What Is This?

AgentTriage is a production-grade agentic system where an AI agent pipeline automatically triages software incidents — the same work a human Site Reliability Engineer (SRE) does when production goes down.

When something breaks in production (a server crashes, a database causes a cascade failure, or a service silently degrades), engineers need to:
1. Diagnose the severity (P1/P2/P3)
2. Identify the root cause (which service/component)
3. Decide on remediation (restart, kill-query, flush-cache)
4. Escalate to the right team

AgentTriage automates this entire workflow using a **multi-agent pipeline** running on **AMD Developer Cloud**.

---

## 🧠 How It Works

### The Environment (LogTriageEnv)
A simulated microservice incident environment with a REST API interface (OpenEnv-compatible). The agent interacts via a reset → step loop, reads logs and service states, takes actions, and gets scored.

**Three incident scenarios:**

| Task | Difficulty | Noise | Incident Type |
|---|---|---|---|
| `single_crash` | Easy | 20% | Payment service NullPointerException |
| `cascading_failure` | Medium | 30% | user-db slow query → auth → gateway cascade |
| `silent_degradation` | Hard | 60% | Gradual payment-db latency increase (no crash) |

### The Agent Pipeline

```
Incoming Logs + Service State
         ↓
   [PLANNER AGENT]
   Reads logs, decides strategy
         ↓
   [EXECUTOR AGENT]
   Takes triage actions step-by-step
   classify_severity → identify_root_cause → remediate → resolve
         ↓
   [SUMMARIZER AGENT]
   Produces structured incident report
         ↓
   Episode Score (0.0 → 1.0)
```

All agents powered by **AMD Developer Cloud** (Qwen2.5-72B on MI300X) with Groq fallback for the live demo.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│              AgentTriage System                  │
│                                                  │
│  ┌──────────────┐     ┌──────────────────────┐  │
│  │  LangGraph   │────▶│   AMD Developer      │  │
│  │  Agent Loop  │     │   Cloud LLM API      │  │
│  │              │◀────│   Qwen2.5-72B        │  │
│  └──────┬───────┘     └──────────────────────┘  │
│         │                                        │
│  ┌──────▼───────┐                               │
│  │  LogTriage   │                               │
│  │  Environment │                               │
│  │  (FastAPI)   │                               │
│  └──────┬───────┘                               │
│         │                                        │
│  ┌──────▼───────────────────────────────────┐   │
│  │          Scenario Engine                  │   │
│  │  single_crash | cascading | silent_degrade│   │
│  └──────┬───────────────────────────────────┘   │
│         │                                        │
│  ┌──────▼───────┐                               │
│  │    Grader    │  → Episode Score (0.0–1.0)    │
│  └──────────────┘                               │
└─────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Agent Framework | LangGraph |
| LLM Backend | AMD Developer Cloud — Qwen2.5-72B on MI300X |
| LLM Fallback | Groq — llama-3.3-70b-versatile |
| Environment API | FastAPI + Uvicorn |
| Data Validation | Pydantic v2 |
| Containerization | Docker |
| Environment Interface | OpenEnv-compatible (reset/step) |
| Language | Python 3.11 |

---

## 📁 Project Structure

```
agentic-triage-amd/
│
├── server/                        # LogTriageEnv (environment core)
│   ├── app.py                     # FastAPI endpoints + UI routes
│   ├── environment.py             # Core simulator (reset/step/state)
│   ├── models.py                  # Pydantic schemas
│   ├── log_generator.py           # Log + service state generation
│   ├── scenarios/
│   │   ├── single_crash.py        # Task 1: Payment service crash
│   │   ├── cascading.py           # Task 2: user-db cascade
│   │   └── silent_degrade.py      # Task 3: Gradual latency degradation
│   └── graders/
│       ├── base_grader.py
│       ├── crash_grader.py
│       ├── cascade_grader.py
│       └── silent_degrade_grader.py
│
├── agents/                        # Multi-agent pipeline
│   ├── planner.py                 # Reads logs, sets strategy
│   ├── executor.py                # Step-by-step triage actions
│   ├── summarizer.py              # Generates incident report
│   └── pipeline.py                # LangGraph orchestration
│
├── static/
│   └── index.html                 # Judge-facing web UI
│
├── amd_client.py                  # LLM client (AMD + Groq fallback)
├── run_agent.py                   # CLI entry point
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## ⚙️ Setup & Running

### Option 1 — Docker (Recommended)

```bash
git clone https://github.com/YOUR_USERNAME/agentic-triage-amd.git
cd agentic-triage-amd
cp .env.example .env
# Add your GROQ_API_KEY or AMD_API_KEY to .env
docker build -t agentic-triage-amd .
docker run -p 7860:7860 --env-file .env agentic-triage-amd
# Open http://localhost:7860
```

### Option 2 — Local Python

```bash
pip install -r requirements.txt
# Terminal 1 — environment server
uvicorn server.app:app --host 0.0.0.0 --port 7860
# Terminal 2 — run agent on all 3 tasks
python run_agent.py
```

---

## 🔑 Environment Variables

```env
# Use one of these — Groq for free tier, AMD for full power
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile

# AMD Developer Cloud VM
AMD_API_KEY=your_amd_api_key
AMD_BASE_URL=http://YOUR_VM_IP:8000/v1
AMD_MODEL=qwen
```

---

## 🧪 Scoring System

Each task scored 0.0 → 1.0:

| Action | Points |
|---|---|
| Correct severity classification | +0.30 |
| Correct root cause identification | +0.35 |
| Correct remediation command | +0.25 |
| Speed bonus (within step threshold) | +0.10 |
| Wrong escalation | -0.10 |
| Ignoring a P1 incident | -0.50 |
| Symptom identified as root cause | -0.10 |

---

## 📊 Results

| Task | Score |
|---|---|
| single_crash | 0.9 |
| cascading_failure | 0.6 |
| silent_degradation | 0.3 |
| **Average** | **0.6** |

---

## 🙋 Team

| Name | Role |
|---|---|
| Rohit Patil (Sonic) | Environment + Agent Pipeline |
| [Teammate] | Infrastructure + AMD VM Setup |

---

## 📄 License

MIT License — open source, built for AMD Developer Cloud Hackathon.

---

> Built with AMD MI300X (192GB VRAM) · Qwen2.5-72B · LangGraph · FastAPI · Docker
