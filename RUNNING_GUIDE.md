# How to Run the Application

Complete step-by-step guide with exact terminal commands to run the **Insurance Verification & Authorization Automation Platform** locally.

**Stack:** FastAPI (Python) + PostgreSQL (Docker) + React/Vite + Ollama (local LLM)

---

## Prerequisites

Ensure the following are installed before starting:

| Tool | Check Command | Required Version |
|------|--------------|-----------------|
| Python | `python --version` | 3.9+ |
| Node.js & npm | `node --version && npm --version` | Node 18+, npm 8+ |
| Docker Desktop | `docker --version` | Any recent version |
| Ollama | `ollama --version` | Any recent version |

---

## Terminal 1 — Start PostgreSQL via Docker

Open a terminal and run:

```powershell
# Pull and start PostgreSQL 16 container
docker run -d `
  --name insurance_postgres `
  -e POSTGRES_USER=postgres `
  -e POSTGRES_PASSWORD=postgres `
  -e POSTGRES_DB=insurance_platform `
  -p 5432:5432 `
  postgres:16-alpine
```

```powershell
# Verify the container is running
docker ps --filter "name=insurance_postgres"
```

> **Note:** If the container already exists from a previous run, start it with:
> ```powershell
> docker start insurance_postgres
> ```

---

## Terminal 2 — Start Ollama LLM (phi3)

Open a **new** terminal and run:

```powershell
# Pull and serve the phi3 model (keep this terminal open)
ollama run phi3
```

> This starts the local AI server at `http://localhost:11434`.
> The first run will download the phi3 model (~2 GB). Subsequent runs are instant.
>
> **Alternative model:** Replace `phi3` with `mistral` if you prefer.

---

## Terminal 3 — Setup & Run the Backend (FastAPI)

Open a **new** terminal and run each command in order:

```powershell
# 1. Navigate to the backend directory
cd "c:\Users\DELL\Downloads\ZeroKost\Insurance AUtomation OCR\ocr_with_CPT_openAI\backend"
```

```powershell
# 2. Create the virtual environment (first time only)
python -m venv venv
```

```powershell
# 3. Activate the virtual environment (Windows)
venv\Scripts\activate
```

```powershell
# 4. Install all Python dependencies (first time only)
pip install -r requirements.txt
```

```powershell
# 5. Download the spaCy NLP model (first time only)
# Use the direct URL — the 'spacy download' command often generates a broken URL
pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl
```

```powershell
# 6. Initialize the database — creates all 7 tables (first time only)
python setup_db.py
```

```powershell
# 7. Start the FastAPI server (keep this terminal open)
uvicorn main:app --reload
```

> Backend API is now live at: **http://localhost:8000**
> Interactive API docs at: **http://localhost:8000/docs**

---

## Terminal 4 — Setup & Run the Frontend (React + Vite)

Open a **new** terminal and run:

```powershell
# 1. Navigate to the frontend directory
cd "c:\Users\DELL\Downloads\ZeroKost\Insurance AUtomation OCR\ocr_with_CPT_openAI\frontend"
```

```powershell
# 2. Install Node dependencies (first time only)
npm install
```

```powershell
# 3. Start the Vite development server (keep this terminal open)
npm run dev
```

> Frontend dashboard is now live at: **http://localhost:5173**

---

## Summary — All 4 Running Processes

Once set up, you need **4 terminals running simultaneously**:

| # | Terminal | Command | URL |
|---|---------|---------|-----|
| 1 | PostgreSQL | `docker start insurance_postgres` | port 5432 |
| 2 | Ollama LLM | `ollama run phi3` | http://localhost:11434 |
| 3 | FastAPI Backend | `uvicorn main:app --reload` | http://localhost:8000 |
| 4 | React Frontend | `npm run dev` | http://localhost:5173 |

---

## Environment Variables (Optional Overrides)

Set these before starting Terminal 3 if your PostgreSQL or Ollama configuration differs:

```powershell
$env:DATABASE_URL  = "postgresql+asyncpg://postgres:postgres@localhost:5432/insurance_platform"
$env:OLLAMA_BASE_URL = "http://localhost:11434/v1"
$env:OLLAMA_MODEL    = "phi3"
```

---

## Quick Restart (After First-Time Setup)

For subsequent runs, you only need these commands:

```powershell
# Terminal 1 — start Postgres
docker start insurance_postgres

# Terminal 2 — start Ollama LLM
ollama run phi3

# Terminal 3 — start backend
cd "c:\Users\DELL\Downloads\ZeroKost\Insurance AUtomation OCR\ocr_with_CPT_openAI\backend"
venv\Scripts\activate
uvicorn main:app --reload

# Terminal 4 — start frontend
cd "c:\Users\DELL\Downloads\ZeroKost\Insurance AUtomation OCR\ocr_with_CPT_openAI\frontend"
npm run dev
```

---

## Stopping the Application

```powershell
# Stop the PostgreSQL container (data is preserved)
docker stop insurance_postgres

# Stop Ollama, backend, and frontend: press Ctrl+C in each terminal
```

```powershell
# To completely remove the PostgreSQL container and all data:
docker rm -f insurance_postgres
```

---

## Troubleshooting

### ❌ `Fatal error in launcher: Unable to create process` (broken venv)

**Cause:** The `venv` was created at a different folder path. Python venvs embed absolute paths and break if the project folder is renamed or moved.

**Fix:** Delete and recreate the venv inside the `backend` folder:

```powershell
deactivate
Remove-Item -Recurse -Force venv
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl
```

### ❌ Backend fails to connect to PostgreSQL

Make sure the Docker container is running:
```powershell
docker ps --filter "name=insurance_postgres"
# If not listed, start it:
docker start insurance_postgres
```

### ❌ `TypeError: Client.__init__() got an unexpected keyword argument 'proxies'`

**Cause:** `openai==1.13.3` passes a `proxies` argument that was removed in `httpx>=0.28.0`.

**Fix:** Downgrade httpx:
```powershell
pip install httpx==0.27.2
```

---

### ❌ Ollama model not found

```powershell
# Pull the model first
ollama pull phi3
# Then run it
ollama run phi3
```
