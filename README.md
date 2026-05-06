# 🔴 AgentTriage — Agentic SRE Incident Response on AMD Developer Cloud

> Multi-agent log triage system that autonomously diagnoses production incidents using AMD-hosted LLMs and a LangGraph-powered agent pipeline.

Built for the **AMD Developer Cloud —  AI Agents & Agentic Workflows**

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

### The Agent Pipeline (New — AMD-Powered)

```
Incoming Logs + Service State
         ↓
   [PLANNER AGENT]
   Reads logs, decides strategy
         ↓
   [EXECUTOR AGENT]
   Takes triage actions step-by-step
   (classify_severity → identify_root_cause → remediate → resolve)
         ↓
   [SUMMARIZER AGENT]
   Produces structured incident report
         ↓
   Episode Score (0.0 → 1.0)
```

All agents run on **AMD Developer Cloud hosted LLMs** (Mistral/Llama) via their OpenAI-compatible API endpoint.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│              AgentTriage System                  │
│                                                  │
│  ┌──────────────┐     ┌──────────────────────┐  │
│  │  LangGraph   │────▶│   AMD Developer      │  │
│  │  Agent Loop  │     │   Cloud LLM API      │  │
│  │              │◀────│   (Mistral/Llama)    │  │
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
| LLM Backend | AMD Developer Cloud (Mistral-7B / Llama-3) |
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
│   ├── app.py                     # FastAPI endpoints (/reset, /step, /state, /tasks)
│   ├── environment.py             # Core simulator (reset/step/state)
│   ├── models.py                  # Pydantic schemas (LogLine, TriageAction, etc.)
│   ├── log_generator.py           # Log + service state generation
│   ├── scenarios/
│   │   ├── single_crash.py        # Task 1: Payment service crash
│   │   ├── cascading.py           # Task 2: user-db → auth → gateway cascade
│   │   └── silent_degrade.py      # Task 3: Gradual latency degradation
│   └── graders/
│       ├── base_grader.py         # Abstract grader interface
│       ├── crash_grader.py        # Task 1 scoring
│       └── cascade_grader.py      # Task 2 scoring
│
├── agents/                        # Multi-agent pipeline (NEW)
│   ├── planner.py                 # Planner agent — reads logs, sets strategy
│   ├── executor.py                # Executor agent — takes step-by-step actions
│   ├── summarizer.py              # Summarizer agent — generates incident report
│   └── pipeline.py                # LangGraph graph definition
│
├── amd_client.py                  # AMD Developer Cloud LLM client
├── run_agent.py                   # Entry point — runs agent on all 3 tasks
├── Dockerfile                     # Container definition
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment variable template
└── README.md                      # This file
```

---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.11+
- Docker
- AMD Developer Cloud account + API key

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/agentic-triage-amd.git
cd agentic-triage-amd
```

### 2. Set environment variables
```bash
cp .env.example .env
# Edit .env — add your AMD_API_KEY
```

### 3. Run with Docker
```bash
docker build -t agentic-triage-amd .
docker run -p 7860:7860 --env-file .env agentic-triage-amd
```

### 4. Run locally
```bash
pip install -r requirements.txt
# Terminal 1 — start the environment
uvicorn server.app:app --host 0.0.0.0 --port 7860
# Terminal 2 — run the agent
python run_agent.py
```

---

## 🧪 Scoring System

Each task is scored 0.0 to 1.0:

| Action | Points |
|---|---|
| Correct severity classification | +0.30 |
| Correct root cause identification | +0.35 |
| Correct remediation command | +0.25 |
| Speed bonus (within step threshold) | +0.10 |
| Wrong escalation | -0.10 |
| Ignoring a P1 incident | -0.50 |

**Task 1:** severity=P1, root_cause=payment-service, remediation=restart:payment-service
**Task 2:** severity=P1, root_cause=user-db, remediation=kill-query:user-db
**Task 3:** severity=P2, root_cause=payment-db, remediation=flush-cache:payment-db

---

## 📊 Results

| Task | Score |
|---|---|
| single_crash | — |
| cascading_failure | — |
| silent_degradation | — |
| **Average** | **—** |

*(Updated after final runs)*

---

## 🔑 Environment Variables

```env
AMD_API_KEY=your_amd_developer_cloud_api_key
AMD_BASE_URL=https://api.amd.com/v1
AMD_MODEL=mistral-7b-instruct
ENV_HOST=0.0.0.0
ENV_PORT=7860
```

---

## ✅ Hackathon Checklist

- [ ] AMD Developer Cloud account activated
- [ ] LLM swap: Groq → AMD hosted model working
- [ ] Planner agent implemented
- [ ] Executor agent implemented
- [ ] Summarizer agent implemented
- [ ] LangGraph pipeline connecting all three agents
- [ ] All 3 tasks running end-to-end
- [ ] Scores recorded and documented
- [ ] Demo video recorded
- [ ] Devpost submission written
- [ ] Repo open-sourced and clean

---

## 🙋 Team

| Name | Role |
|---|---|
| Rohit Patil (Sonic) | Environment + Agent Pipeline |
| [Teammate] | [Role TBD] |

---

## 📄 License

MIT License — open source, built for AMD Developer Cloud Hackathon.

---

> **Note:** This project builds on prior research work in agentic log triage environments, redesigned and upgraded with a multi-agent architecture specifically for AMD Developer Cloud infrastructure.
