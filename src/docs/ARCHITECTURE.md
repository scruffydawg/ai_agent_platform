# ⚙️ ARCHITECTURE DEEP DIVE
> How the AI Agent Platform works under the hood.

---

## 🔄 THE COMPLETE DATA FLOW

### 🗣️ WHEN YOU SEND A MESSAGE

```
YOU TYPE + HIT SEND
        │
        ▼
  App.jsx handleRun()
        │
        ├─ 1. setAgentStatus('thinking')    [UI → THINKING spinner]
        ├─ 2. Append user msg to messages[] [UI → shows your message]
        │
        ▼
  POST http://[hostname]:8001/chat
  {
    prompt: "your message",
    history: [last 20 messages]
  }
        │
        ▼
  server.py /chat endpoint
        │
        ├─ Loads GUIDE system prompt (workspace-aware)
        ├─ Loads recent file context from FileSystemSkill
        ├─ Calls Ollama LLM (streaming)
        │
        ▼
  Server-Sent Events (SSE) stream back to browser
  data: {"content": "GUIDE..."} chunks
        │
        ▼
  App.jsx reads stream chunk by chunk
        │
        ├─ Updates assistant message in real-time
        ├─ setAgentStatus('idle')            [UI → IDLE dot]
        └─ Saves message to session JSON
```

---

### 🔴 REAL-TIME HEARTBEAT (WebSocket)

```
Browser connects:
  ws://[hostname]:8001/stream

Every ~2 seconds server sends:
  {"type": "heartbeat", "halted": false}

If KILL SWITCH is hit:
  {"type": "heartbeat", "halted": true}

Canvas push event:
  {"type": "canvas_push", "mode": "MD", "content": "..."}
  → App.jsx fires window.dispatchEvent('canvas-push')
  → CanvasPanel.jsx catches it and renders content
  → Canvas auto-opens at 25/75 split
```

---

### 📊 SWARM DASHBOARD POLLING

```
SwarmView.jsx
  │
  └─ Every 2000ms:
       GET http://[hostname]:8001/swarm/status
       →  {
            "tai_mae": {cpu: 8, ram: 32, gpu: 45, ...},
            "sienna":  {cpu: 15, ram: 32, ...},
            "dash":    {cpu: 5, ram: 12, ...},
            "pi":      {cpu: 82, ram: 60, ...}
          }
       → Renders NodeCard components with animated metric bars
```

---

### 🔧 TOOL REGISTRY FLOW

```
ToolRegistry.jsx
  │
  ├─ On mount:
  │    GET /tools/registry
  │    → [{name, type, description, icon, status, filename}, ...]
  │
  └─ On card click (openEditor):
       IF has filename:
         GET /tools/source?filename=n8n_control.py
         → {status: "success", content: "import httpx..."}
         → parsePythonScript() extracts methods
         → Renders Visual Map (ADHD mode) or Raw Code textarea
       ELSE (MCP / Code Tool):
         → Shows capability overview only
```

---

## 🏗️ BACKEND API ENDPOINTS

| Method | Endpoint | What it does |
|--------|----------|-------------|
| `GET` | `/sessions` | List all chat sessions |
| `POST` | `/sessions/new` | Create new session |
| `GET` | `/sessions/{id}` | Load session messages |
| `POST` | `/sessions/{id}/message` | Append message + auto-title |
| `POST` | `/chat` | Stream LLM response (SSE) |
| `WS` | `/stream` | Real-time heartbeat + canvas push |
| `GET` | `/swarm/status` | Node telemetry (CPU/RAM/GPU) |
| `GET` | `/swarm/experts` | List active expert agents |
| `GET` | `/swarm/expert/{name}` | Load expert .md soul |
| `POST` | `/swarm/expert/{name}` | Save expert .md soul |
| `POST` | `/swarm/expert/spawn` | Create new expert agent |
| `DELETE` | `/swarm/expert/{name}` | Remove expert agent |
| `GET` | `/tools/registry` | List all tools + skills |
| `GET` | `/tools/source` | Get Python source code |
| `POST` | `/tools/source` | Save edited source code |
| `GET` | `/config` | Load runtime config |
| `POST` | `/config` | Save runtime config |
| `GET` | `/ollama/models` | List available Ollama models |
| `POST` | `/storage/init` | Initialize storage directories |
| `POST` | `/canvas/event` | Trigger canvas push event |

---

## 🔐 SECURITY MODEL

```
AGENT_API_KEY env var
  │
  ├─ Not set? → All endpoints open (local dev mode)
  └─ Set?     → require_auth() dependency on all routes
                 Checks: Authorization: Bearer <key>
                 Works on: HTTP requests AND WebSocket upgrades
```

> **CORS Policy:**
> `allow_origins=["*"]` — open to all LAN origins.
> Acceptable for local/home network deployment.
> Lock this down before exposing to internet.

---

## 🧩 EXPERT AGENT SYSTEM

```
src/agents/experts/
├── Architect.md    ← System design expert soul
├── Security.md     ← Security auditor soul
├── ADHD_UX.md      ← UX clarity expert soul
├── Analyst.md      ← Data analysis soul
├── Observer.md     ← Monitoring expert soul
└── Researcher.md   ← Research synthesis soul

Each .md file = the expert's "soul" — their personality,
capabilities, directives, and knowledge base.

persona_loader.py reads these at runtime and injects
them as system context into the LLM when that expert
is activated in the swarm.
```

---

## 🎨 FRONTEND DESIGN SYSTEM

### CSS Variables (index.css)
```css
--bg-color          ← Page background
--panel-bg          ← Card/panel background
--header-bg         ← Header bar background
--text-primary      ← Main text
--text-secondary    ← Dimmed text
--border-color      ← Subtle borders
--accent-cyan       ← Primary accent (skills, info)
--accent-purple     ← MCP / special features
--accent-ochre      ← GUIDE / highlights / headers
--accent-green      ← Online / success states
--accent-red        ← Error / kill switch / offline
--card-shadow       ← Elevation shadow
```

### Themes
- 🌑 **Dark Mode** — default, easy on eyes, neon accents
- ☀️ **Light Mode** — "Vibrant Light" — high contrast, warm tones

### Key Components
| Component | Purpose |
|-----------|---------|
| `status-pill` | GUIDE thinking/idle/error indicator |
| `status-dot` | Animated pulse dot |
| `card` | Glass-effect content panel |
| `button-primary` | Main action button (ochre) |
| `button-secondary` | Secondary action (bordered) |
| `status-pulse` | Live data indicator (green pulse) |
