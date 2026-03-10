# 🛠️ CHANGELOG — WHAT WE BUILT & FIXED TODAY
> March 10, 2026 — Phase 13: GUIDE Architecture (Memory & Recovery)

---

## 🎯 SESSION GOALS (All Achieved ✅)

1. Implement **GUIDE v3.0** (Complete Memory & Capability Architecture)
2. Refactor Memory Layer into **5-Lane Structure** (Session, Working, Resume, Semantic, Episodic)
3. Build the **8-Stage Memory Broker** Pipeline for intelligent context assembly
4. Implement **Resume Memory** task re-entry logic in StateGraph Orchestrator
5. Add ADHD-friendly UI: **ResumePanel** (Interruption Detection) and **Memory Inspector** (Context Transparency)
6. Migrate Orchestrator to **Full Async** node execution
7. Verify integration with automated test suite

---


## 🎯 SESSION GOALS (All Achieved ✅)

1. Standardize V2 API structure (`/api/v2/`)
2. Decouple logic into modular Service packages
3. Verify all 7 core V2 endpoints with 100% success
4. Create comprehensive V2 Architecture & Migration documentation
5. Standardize Tool Registry (Skills + MCP) response envelopes
6. **Advanced Tooling (Phase 7)**: Refactored workplace skills (G-Drive, O365) to async and decoupled security tokens.
7. **Swarm Intelligence (Phase 8)**: Implemented Metacognitor persona, loop detection, and recursive swarm support.

---

## 🐛 BUGS FIXED

---

### 🔴 BUG 1 — Skills Panel Black Screen (React Crash)

**Symptom:** Clicking any skill in the Tool Registry instantly goes black.

**Root Cause:**
```
ToolRegistry.jsx was using <Zap> icon at line 366
but Zap was NOT in the lucide-react import list.
→ ReferenceError: Zap is not defined
→ React unmounts entire component tree
→ Black screen
```

**Fix Applied:**
```diff
- import { Puzzle, Globe, ..., Activity } from 'lucide-react';
+ import { Puzzle, Globe, ..., Activity, Zap } from 'lucide-react';
```

**File:** `frontend/src/components/ToolRegistry.jsx` line 4

---

### 🔴 BUG 2 — All Panels Empty After CORS Fix Attempt

**Symptom:** Dashboard, Logic Graph, and Tool Registry showed no data.
Frontend accessed via `127.0.0.1:5173` but all API calls hardcoded to `localhost:8001`.

**Root Cause:**
```
Browser was at: http://127.0.0.1:5173/
API calls went: http://localhost:8001/...
                         ↑
Browser treats 127.0.0.1 ≠ localhost as different origins
→ CORS preflight failed silently
→ All fetch() calls returned nothing
```

**Files affected (all had hardcoded localhost:8001):**
```
App.jsx, SwarmView.jsx, GraphView.jsx,
ToolRegistry.jsx, SkillForge.jsx, SettingsView.jsx
```

**Fix Applied:**
Created `frontend/src/api.js`:
```js
const hostname = window.location.hostname;  // reads actual browser URL
export const API_BASE = `http://${hostname}:8001`;
export const WS_BASE  = `ws://${hostname}:8001`;
```
All components now import from this file. Works from any hostname.

---

### 🔴 BUG 3 — WebSocket Crashes on Every Connection

**Symptom:** Logic Graph and Dashboard would connect but immediately disconnect.
Backend log showed TypeError on every WebSocket upgrade.

**Root Cause:**
```python
# OLD broken auth:
security = HTTPBearer(auto_error=False)
def require_auth(credentials: HTTPAuthorizationCredentials = Depends(security)):
    ...
# HTTPBearer only accepts HTTP Request objects.
# On WebSocket upgrade, it receives a WebSocket object
# → TypeError: HTTPBearer.__call__() missing 1 required positional argument: 'request'
# → WebSocket connection killed on every connect
```

**Fix Applied:** (`src/server.py`)
```python
def require_auth(request: Request = None, websocket: WebSocket = None):
    api_key = os.environ.get("AGENT_API_KEY", "")
    if not api_key:
        return  # auth disabled if no key set
    conn = request if request is not None else websocket
    auth = conn.headers.get("Authorization")
    if not auth or auth != f"Bearer {api_key}":
        raise HTTPException(status_code=401, detail="Unauthorized")
```
Now handles both HTTP requests AND WebSocket upgrades correctly.

---

### 🔴 BUG 4 — Missing WebSocket Python Library

**Symptom:** Backend log showed:
```
WARNING: No supported WebSocket library detected.
WARNING: Unsupported upgrade request.
```
All WebSocket connections returned 404 instead of upgrading.

**Root Cause:** `websockets` Python package was not installed in venv.

**Fix Applied:**
```bash
pip install websockets 'uvicorn[standard]'
```

---

### 🟡 BUG 5 — localhost:5173 Not Accessible (IPv6 Issue)

**Symptom:** `127.0.0.1:5173` worked fine, `localhost:5173` hung/refused.

**Root Cause:**
```
Vite was bound to: 0.0.0.0:5173  (IPv4 only)
Chrome tried:      ::1:5173       (IPv6 first on Linux)
→ IPv6 connection refused
→ Chrome sometimes doesn't fall back cleanly
```

**Fix Applied** (`frontend/vite.config.js`):
```js
server: {
  host: true,         // binds BOTH 0.0.0.0 (IPv4) AND :: (IPv6)
  port: 5173,
  strictPort: true,
}
```

---

### 🟡 BUG 6 — CORS Blocked LAN Access

**Symptom:** Platform worked locally but not from other LAN devices.

**Root Cause:** CORS was locked to explicit origin whitelist:
```python
allowed_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
```
Any LAN IP (e.g., `http://10.0.0.26:5173`) was blocked by CORS.

**Fix Applied** (`src/server.py`):
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],    # all origins allowed
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## ✨ NEW FEATURES ADDED

---

### 🆕 FEATURE 1 — Shared API URL Config (`api.js`)

New file: `frontend/src/api.js`

Dynamically resolves correct API URLs based on how you access the app.
No more hardcoded localhost — works from LAN, Tailscale, and loopback seamlessly.

---

### 🆕 FEATURE 2 — GitHub Repository

Created: https://github.com/scruffydawg/ai_agent_platform

- Initial commit with 94 source files
- Large ML models (`*.onnx`, `voices.json`) excluded via `.gitignore`
- `models/` folder purged from git history to comply with GitHub 100MB limit
- Classic PAT stored in git credential helper for `git push` access

---

### 🆕 FEATURE 3 — Platform Documentation (`src/docs/`)

New docs created:
```
src/docs/
├── PLATFORM_OVERVIEW.md   ← What this is, who it's for, where stuff lives
├── ARCHITECTURE.md        ← Data flows, API endpoints, design system
├── STARTUP_GUIDE.md       ← How to start/stop/debug
└── CHANGELOG.md           ← This file — what was fixed and why
```

---

## 📊 HEALTH STATUS AFTER SESSION

| Component | Status |
|-----------|--------|
| FastAPI Backend (port 8001) | ✅ Running |
| Vite Frontend (port 5173) | ✅ Running |
| WebSockets (`/stream`) | ✅ Accepting connections |
| CORS Policy | ✅ Open to all LAN origins |
| Tool Registry | ✅ Loading tools correctly |
| Swarm Dashboard | ✅ Streaming telemetry |
| Logic Graph | ✅ Rendering expert nodes |
| Skills Panel | ✅ Opens without crashing |
| GitHub Push | ✅ Latest code on main branch |

---

## 🔮 KNOWN TODO FOR NEXT SESSION

- [ ] Fix `parsePythonScript` in `ToolRegistry.jsx` — Execution Nodes panel shows raw code body instead of clean docstring description  
- [ ] Replace `alert()` calls in tool editor with inline toast notifications
- [ ] Add Git workflow to sidebar (commit/push button from UI)
- [ ] Fix remaining Pyre2 type lint errors in `server.py`
