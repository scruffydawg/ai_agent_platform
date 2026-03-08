# 🧠 AI AGENT PLATFORM — PLATFORM OVERVIEW
> **"THE FLUTE PATH IS CLEAR."** — Built by ScruffyDawg. Powered by GUIDE.

---

## 🗺️ WHAT IS THIS?

This is a **self-hosted, LAN-accessible, ADHD-optimized AI Agent Platform** built from scratch. It is:

- 🦾 A **multi-agent orchestration engine** (GUIDE + Expert Swarm)
- 🧠 **Adaptive Memory** (Long-term pattern recognition & self-learning)
- 🌐 A **web dashboard** you can access from any device on your LAN
- 🔧 A **tool & skill registry** with **Contextual Consult** AI guidance
- 📊 A **real-time systems monitor** for your computing mesh
- 🎨 A **canvas workspace** for code, docs, and ideas

---

## ⚡ THE BIG PICTURE — ONE GLANCE

```
┌─────────────────────────────────────────────────────────────┐
│                    YOUR BROWSER (any device)                 │
│                    http://10.0.0.26:5173                     │
└──────────────────────────┬──────────────────────────────────┘
                           │
                    ┌──────▼──────┐
                    │  VITE DEV   │  ← React UI
                    │ PORT: 5173  │   (frontend/)
                    └──────┬──────┘
                           │ HTTP + WebSocket
                    ┌──────▼──────┐
                    │   FastAPI   │  ← Python Backend
                    │ PORT: 8001  │   (src/server.py)
                    └──────┬──────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
    ┌─────▼────┐    ┌──────▼─────┐   ┌─────▼────┐
    │  OLLAMA  │    │   Qdrant   │   │ Postgres │
    │ (LLM AI) │    │ (Memory)   │   │  (Data)  │
    └──────────┘    └────────────┘   └──────────┘
```

---

## 🎭 MEET THE CAST

### 🌟 GUIDE (Your AI Assistant)
> *"Ehecatl, the Wind of Thought"* — always present in the chat terminal

- Knows about your entire workspace and file system
- Aware of all active skills and MCP tools
- Can autonomously push content to the Canvas
- Runs on your local Ollama instance

### 🐝 THE SWARM EXPERTS
| Expert | Role | Color Code |
|--------|------|-----------|
| **Architect** | System design & structure | 🟡 Ochre |
| **Security** | Code auditing & access control | 🔴 Red |
| **ADHD_UX** | Interface clarity & flow | 🔵 Cyan |
| **Analyst** | Data patterns & insights | 🟢 Green |
| **Observer** | Monitoring & state tracking | ⚪ White |
| **Researcher** | Web search & knowledge synthesis | 🟣 Purple |

---

## 📱 THE UI — 5 MAIN VIEWS

```
SIDEBAR NAV
├── 💬  CHAT          (Observer Terminal with GUIDE)
├── 🕸️  LOGIC GRAPH   (Visual Swarm Mind Map)
├── 🖥️  DASHBOARD     (Swarm Node Telemetry)
├── 🔧  TOOL REGISTRY (Skills + MCPs + Code Tools)
├── ⚒️  SKILL FORGE   (AI-assisted skill creator)
└── ⚙️  SETTINGS      (Config + LLM + Storage)
```

---

## 🔌 THE TOOLS — 3 TYPES

### 🐍 Native Skills
Python classes in `src/skills/` — directly executed by the agent.
```
voice_in.py    → Whisper STT (speech-to-text)
voice_out.py   → Kokoro TTS (text-to-speech)
web_search.py  → SearXNG web search
file_system.py → Workspace file operations
vision.py      → Screenshot + OCR
n8n_control.py → n8n workflow API control
gmail.py       → Gmail integration
google_drive.py → Google Drive integration
office_365.py  → Microsoft Graph API
docker_management.py → Docker skill
```

### 🌐 MCP Servers
External Model Context Protocol servers
```
n8n-mcp → n8n workflow automation server
```

### 💎 Code Tools
Dynamically generated tools stored in `canvas_artifacts/`

---

## 🌍 NETWORK ACCESS

| URL | Where from |
|-----|-----------|
| `http://localhost:5173` | This machine |
| `http://127.0.0.1:5173` | This machine (alternate) |
| `http://10.0.0.26:5173` | Your local network (LAN) |
| `http://100.114.169.66:5173` | Tailscale VPN mesh |

> ✅ All devices on your network can reach the UI fully!

---

## 🗂️ WHERE DOES STUFF LIVE?

```
ai_agent_platform/
├── frontend/          ← React UI (Vite)
│   └── src/
│       ├── App.jsx        ← Main app shell + routing
│       ├── api.js         ← Shared API URL config (dynamic!)
│       ├── index.css      ← Full design system / tokens
│       └── components/
│           ├── ToolRegistry.jsx   ← Tool viewer + editor
│           ├── GraphView.jsx      ← Swarm mind map
│           ├── SwarmView.jsx      ← Systems dashboard
│           ├── SkillForge.jsx     ← Skill creator
│           ├── CanvasPanel.jsx    ← Workspace canvas
│           └── SettingsView.jsx   ← Config UI
│
├── src/               ← Python Backend
│   ├── server.py          ← FastAPI entrypoint
│   ├── config.py          ← App config + settings
│   ├── skills/            ← All native skills
│   ├── agents/            ← Expert .md souls + loaders
│   │   └── experts/       ← Architect.md, Security.md, etc.
│   ├── core/              ← Orchestrator + state graph
│   ├── memory/            ← Qdrant / in-memory stores
│   ├── llm/               ← Ollama LLM client
│   ├── mcp/               ← MCP protocol client
│   ├── routers/           ← API route modules
│   │   └── tools.py       ← /tools/registry endpoint
│   └── docs/              ← 📖 YOU ARE HERE
│
└── data/              ← Runtime data (git-ignored)
    ├── sessions/      ← Chat history
    ├── memory/        ← Agent memory snapshots
    └── vision/        ← Screenshot captures
```
