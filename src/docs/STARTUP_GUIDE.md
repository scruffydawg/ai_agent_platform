# 🚀 STARTUP GUIDE — HOW TO RUN THE PLATFORM
> Everything you need to go from zero to GUIDE online.

---

## ✅ PRE-FLIGHT CHECKLIST

Before starting, confirm these are running:

- [ ] **Ollama** — `ollama serve` (LLM backend)
- [ ] **Qdrant** — vector memory (if using)
- [ ] **PostgreSQL** — persistent data (if using)
- [ ] **n8n** — `http://localhost:5678` (if using workflows)

---

## 🟢 STARTING THE PLATFORM

### Step 1 — Activate Python Environment
```bash
cd /home/scruffydawg/gemini_workspace/ai_agent_platform
source venv/bin/activate
```

### Step 2 — Start the Backend API
```bash
python -m src.server > backend.log 2>&1 &
```
✅ You should see:
```
INFO: Uvicorn running on http://0.0.0.0:8001
INFO: Application startup complete.
```

### Step 3 — Start the Frontend UI
```bash
cd frontend
npm run dev
```
✅ You should see:
```
VITE v7.3.1  ready in 91 ms
  ➜  Local:   http://localhost:5173/
  ➜  Network: http://10.0.0.26:5173/
```

### Step 4 — Open Your Browser
- **On this machine:** http://localhost:5173
- **On any LAN device:** http://10.0.0.26:5173
- **Via Tailscale:** http://100.114.169.66:5173

---

## 🔄 STOPPING THE PLATFORM

```bash
# Kill backend
kill -9 $(lsof -t -i:8001)

# Kill frontend (Ctrl+C in the npm terminal, or:)
kill -9 $(lsof -t -i:5173)
```

---

## 🧭 DEBUGGING — QUICK DIAGNOSTICS

### Is the backend alive?
```bash
curl http://localhost:8001/swarm/status
# Expected: JSON with node telemetry data
```

### Are sessions working?
```bash
curl http://localhost:8001/sessions
# Expected: {"sessions": [...]}
```

### Is the Tool Registry loading?
```bash
curl http://localhost:8001/tools/registry
# Expected: JSON array of tools
```

### Check backend logs
```bash
cat backend.log | tail -30
```

### Check if ports are in use
```bash
lsof -i :8001   # backend
lsof -i :5173   # frontend
```

### Force-kill a stuck port
```bash
kill -9 $(lsof -t -i:8001)
kill -9 $(lsof -t -i:5173)
```

---

## ⚠️ KNOWN GOTCHAS

### 🔶 "localhost doesn't work but 127.0.0.1 does"
**Cause:** Chrome on Linux tries IPv6 for `localhost` first.
**Fix:** Vite now uses `host: true` — binds both IPv4 + IPv6. Just restart Vite.

### 🔶 "Tool Registry shows nothing"
**Cause:** Frontend is making API calls to wrong origin.
**Fix:** The `api.js` file dynamically reads `window.location.hostname`. 
Ensure you access the UI from one URL consistently.

### 🔶 "Dashboard / Logic Graph not showing data"
**Cause:** WebSocket connection to `/stream` failed.
**Check:** `cat backend.log` — look for WebSocket errors.
**Fix:** Restart backend with `python -m src.server`.

### 🔶 "Backend port already in use"
```bash
kill -9 $(lsof -t -i:8001) && python -m src.server > backend.log 2>&1 &
```

### 🔶 "Skills panel shows black screen when clicked"
**Cause:** A missing JS icon import (`Zap`) crashed the React overlay.
**Status:** ✅ Fixed — `Zap` is now imported in `ToolRegistry.jsx`

### 🔶 "WebSocket connections rejected"
**Cause:** Missing `websockets` Python package.
**Fix:**
```bash
source venv/bin/activate
pip install websockets 'uvicorn[standard]'
python -m src.server > backend.log 2>&1 &
```

---

## 🔧 COMMITTING CHANGES TO GITHUB

When I say "commit and push", or when you want to save your work:
```bash
cd /home/scruffydawg/gemini_workspace/ai_agent_platform
git add -A
git commit -m "your message here"
git push origin main
```

**Repository:** https://github.com/scruffydawg/ai_agent_platform

---

## 📦 ENVIRONMENT (.env file)

```bash
# LLM Backend
LLM_BASE_URL=http://localhost:11434

# Optional API Security (leave empty to disable)
AGENT_API_KEY=

# External Services
SEARXNG_URL=http://localhost:8080
QDRANT_URL=http://localhost:6333
POSTGRES_URL=postgresql://user:pass@localhost/db

# Storage Root
DEFAULT_STORAGE_ROOT=/home/scruffydawg/gemini_workspace
```
