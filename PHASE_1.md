# PHASE 1 — Repo Setup + Environment Port + AMD LLM Swap

> **Goal:** New repo created, old codebase copied cleanly, AMD Developer Cloud LLM working as a drop-in replacement for Groq. Environment boots, `/health` responds, and a test LLM call returns a valid response.
>
> **Time budget:** Day 1 (full day)
>
> **Success condition:** `curl http://localhost:7860/health` returns ok AND `python amd_client.py` returns a valid LLM response from AMD.

---

## STEP 1 — Create the New GitHub Repo

### 1.1 Create repo on GitHub
- Go to https://github.com/new
- Name: `agentic-triage-amd`
- Visibility: **Public**
- Initialize with: **nothing** (no README, no .gitignore)
- Click **Create repository**

### 1.2 Clone it locally
```bash
cd ~/projects   # or wherever you keep your code
git clone https://github.com/YOUR_USERNAME/agentic-triage-amd.git
cd agentic-triage-amd
```

### 1.3 Set up base folder structure
```bash
mkdir -p server/scenarios server/graders agents
touch amd_client.py run_agent.py .env.example
```

**Checklist:**
- [ ] Repo created on GitHub as Public
- [ ] Cloned locally
- [ ] Folder structure created

---

## STEP 2 — Copy Core Files from Old Repo

### 2.1 Copy the server directory
From inside `agentic-triage-amd/`, run:

```bash
cp ../logtriage-env/server/app.py ./server/
cp ../logtriage-env/server/environment.py ./server/
cp ../logtriage-env/server/models.py ./server/
cp ../logtriage-env/server/log_generator.py ./server/
cp ../logtriage-env/server/scenarios/single_crash.py ./server/scenarios/
cp ../logtriage-env/server/scenarios/cascading.py ./server/scenarios/
cp ../logtriage-env/server/scenarios/silent_degrade.py ./server/scenarios/
cp ../logtriage-env/server/graders/base_grader.py ./server/graders/
cp ../logtriage-env/server/graders/crash_grader.py ./server/graders/
cp ../logtriage-env/server/graders/cascade_grader.py ./server/graders/
cp ../logtriage-env/Dockerfile ./
cp ../logtriage-env/requirements.txt ./
```

> Adjust the `../logtriage-env/` path  to "C:\Users\Rohit\Desktop\logtriage-env"  because we need to copy files from here 
### 2.2 Create `__init__.py` files
```bash
touch server/__init__.py
touch server/scenarios/__init__.py
touch server/graders/__init__.py
touch agents/__init__.py
```

### 2.3 Verify structure
```bash
find . -type f -name "*.py" | sort
```

Expected output:
```
./agents/__init__.py
./amd_client.py
./run_agent.py
./server/__init__.py
./server/app.py
./server/environment.py
./server/graders/__init__.py
./server/graders/base_grader.py
./server/graders/cascade_grader.py
./server/graders/crash_grader.py
./server/log_generator.py
./server/models.py
./server/scenarios/__init__.py
./server/scenarios/cascading.py
./server/scenarios/single_crash.py
./server/scenarios/silent_degrade.py
```

**Checklist:**
- [ ] All server files copied
- [ ] All grader files copied
- [ ] All scenario files copied
- [ ] `__init__.py` files created in all 4 directories

---

## STEP 3 — Update requirements.txt

Replace the entire content of `requirements.txt` with:

```txt
# Environment
fastapi>=0.104.0
uvicorn>=0.24.0
pydantic>=2.0.0
openenv-core==0.2.3

# HTTP
requests>=2.25.0
httpx>=0.24.0

# LLM + Agents
openai>=1.0.0
langgraph>=0.1.0
langchain>=0.2.0
langchain-openai>=0.1.0

# Utilities
python-dotenv>=1.0.0
```

Install:
```bash
pip install -r requirements.txt
```

Verify:
```bash
python -c "import fastapi; import langgraph; import openai; print('All packages OK')"
```

**Checklist:**
- [ ] `requirements.txt` updated (Groq removed, LangGraph added)
- [ ] `pip install` completes without errors
- [ ] Verification print shows `All packages OK`

---

## STEP 4 — AMD Developer Cloud Setup

### 4.1 Get your AMD API key
- Go to https://www.amd.com/en/developer/resources/ml-software/developer-cloud.html
- Sign up / log in to AMD Developer Cloud
- Navigate to API Keys section in the dashboard
- Generate a new key — copy it immediately

### 4.2 Note your model and base URL
- In the dashboard, find the Inference / API section
- Note down exactly:
  - The base URL (e.g. `https://api.amd.com/v1`)
  - Available model names (e.g. `mistral-7b-instruct`, `llama-3-8b-instruct`)

### 4.3 Create `.env`
```bash
cat > .env << EOF
AMD_API_KEY=your_actual_key_here
AMD_BASE_URL=https://api.amd.com/v1
AMD_MODEL=mistral-7b-instruct
ENV_HOST=0.0.0.0
ENV_PORT=7860
EOF
```

### 4.4 Create `.env.example` (safe to commit)
```bash
cat > .env.example << EOF
AMD_API_KEY=your_amd_developer_cloud_api_key
AMD_BASE_URL=https://api.amd.com/v1
AMD_MODEL=mistral-7b-instruct
ENV_HOST=0.0.0.0
ENV_PORT=7860
EOF
```

### 4.5 Create `.gitignore`
```bash
cat > .gitignore << EOF
.env
__pycache__/
*.pyc
*.pyo
.DS_Store
*.egg-info/
dist/
build/
.venv/
venv/
EOF
```

**Checklist:**
- [ ] AMD Developer Cloud account active
- [ ] API key obtained and saved
- [ ] Base URL and model name confirmed from dashboard
- [ ] `.env` created with real values
- [ ] `.env.example` created
- [ ] `.gitignore` created

---

## STEP 5 — Write amd_client.py

Open `amd_client.py` and paste this:

```python
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


def get_amd_client() -> OpenAI:
    """Returns an OpenAI-compatible client pointed at AMD Developer Cloud."""
    return OpenAI(
        api_key=os.environ["AMD_API_KEY"],
        base_url=os.environ["AMD_BASE_URL"],
    )


def call_amd_llm(
    prompt: str,
    system_prompt: str = None,
    temperature: float = 0.2
) -> str:
    """
    Single LLM call to AMD Developer Cloud.
    Returns the response text as a plain string.
    """
    client = get_amd_client()
    model = os.environ.get("AMD_MODEL", "mistral-7b-instruct")

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=1024,
    )

    return response.choices[0].message.content.strip()


if __name__ == "__main__":
    # Quick connection test
    print("Testing AMD Developer Cloud connection...")
    result = call_amd_llm(
        prompt=(
            "A payment-service is throwing NullPointerException. "
            "Error rate is 100%. All downstream services are timing out. "
            "What severity is this? Answer with P1, P2, or P3 only."
        ),
        system_prompt="You are an expert Site Reliability Engineer. Be concise."
    )
    print(f"\nAMD LLM Response: {result}")
    print("\nConnection test PASSED." if result else "Connection test FAILED.")
```

### Run the test:
```bash
python amd_client.py
```

Expected output:
```
Testing AMD Developer Cloud connection...

AMD LLM Response: P1

Connection test PASSED.
```

Any coherent text response means the AMD connection works.

**Checklist:**
- [ ] `amd_client.py` written
- [ ] `python amd_client.py` runs without errors
- [ ] AMD LLM returns a valid response
- [ ] No 401/403/404 errors

---

## STEP 6 — Verify the Environment Boots

### 6.1 Start the FastAPI server
```bash
uvicorn server.app:app --host 0.0.0.0 --port 7860 --reload
```

Watch the terminal — it should say `Application startup complete.`

### 6.2 Test all endpoints (new terminal)
```bash
# Health check
curl http://localhost:7860/health

# List tasks
curl http://localhost:7860/tasks

# Reset to single_crash task
curl -X POST http://localhost:7860/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": "single_crash", "seed": 42}'
```

Expected:
- `/health` → `{"status": "ok"}`
- `/tasks` → JSON array with 3 task objects
- `/reset` → Observation JSON with `logs`, `service_state`, `reward`, `done` fields

If `/reset` returns a proper observation with logs — the environment is fully working.

**Checklist:**
- [ ] Server starts with no import errors
- [ ] `/health` returns ok
- [ ] `/tasks` returns 3 tasks
- [ ] `/reset` with `single_crash` returns an observation with logs

---

## STEP 7 — Add README and First Git Push

### 7.1 Add the README
Copy the `README.md` from the files provided into the repo root. Update:
- Replace `YOUR_USERNAME` with your actual GitHub username
- Fill in your teammate's name in the Team table

### 7.2 Commit and push everything
```bash
# Stage all files
git add .

# Verify .env is NOT being staged
git status
# You should NOT see .env in the list — if you do, check .gitignore

# Initial commit
git commit -m "Phase 1: Repo setup, environment port, AMD LLM client"

# Push to GitHub
git push origin main
```

### 7.3 Verify on GitHub
- Open the repo on GitHub
- Confirm all files are there
- Confirm `.env` is NOT visible (only `.env.example` should be there)

**Checklist:**
- [ ] README added with correct username
- [ ] `git status` does NOT show `.env`
- [ ] Committed with descriptive message
- [ ] `git push` successful
- [ ] Repo looks clean on GitHub

---

## PHASE 1 COMPLETE — Final Verification

Run through every item before calling Phase 1 done:

- [ ] `agentic-triage-amd` repo exists on GitHub (Public)
- [ ] All server/ files present and importable
- [ ] LangGraph and openai installed without errors
- [ ] `.env` has real AMD credentials
- [ ] `python amd_client.py` → valid LLM response from AMD
- [ ] `uvicorn server.app:app` starts cleanly
- [ ] `/health` → ok
- [ ] `/tasks` → 3 tasks returned
- [ ] `/reset` → observation with logs returned
- [ ] `.env` NOT committed to GitHub
- [ ] First commit pushed successfully

---

## Troubleshooting

**`ModuleNotFoundError: No module named 'server'`**
```bash
# Always run from the project root directory
cd agentic-triage-amd
uvicorn server.app:app --host 0.0.0.0 --port 7860
```

**`AMD API returns 401 Unauthorized`**
- Double check `AMD_API_KEY` in `.env` — no extra spaces or quotes
- Confirm `python-dotenv` is installed and `load_dotenv()` is called
- Verify the key is active in the AMD Developer Cloud dashboard

**`AMD API returns 404 Not Found`**
- The model name might be wrong — check exact names in AMD dashboard
- Update `AMD_MODEL` in `.env` to match the exact available model string

**`AMD API returns connection error`**
- Check `AMD_BASE_URL` — get the exact URL from the dashboard, don't guess

**`ImportError` on any scenario or grader file**
- Check `__init__.py` exists in `server/`, `server/scenarios/`, `server/graders/`, `agents/`
```bash
find . -name "__init__.py"
```

**Port 7860 already in use**
```bash
# Kill whatever is on that port
lsof -i :7860
kill -9 <PID>
```

---

## What's Next — Phase 2 Preview

Phase 2 builds the three agents:
- `agents/planner.py` — reads the initial observation, outputs a triage strategy
- `agents/executor.py` — loops through steps, calls the environment, takes actions
- `agents/summarizer.py` — takes the completed episode, generates an incident report
- `agents/pipeline.py` — LangGraph graph wiring all three together

**Once all Phase 1 checkboxes are ticked, share your summary and we build Phase 2.**
