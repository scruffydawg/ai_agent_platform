from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional
import asyncio
import json
import os
import time

from src.core.orchestrator import StateGraphOrchestrator
from src.core.state_schema import AgentState
from src.core.state import state_manager
from src.utils.logger import logger
from src.skills.voice_in import voice_stt
from src.skills.voice_out import voice_tts
from src.skills.swarm_telemetry import swarm_telemetry
from src.skills.web_search import web_search
from src.skills.browser_proxy import browser_proxy
from src.config import DEFAULT_MODEL, LLM_BASE_URL, SEARXNG_URL, QDRANT_URL, POSTGRES_URL, DEFAULT_STORAGE_ROOT
from src.skills.file_system import FileSystemSkill
from src.agents.skill_builder import skill_builder
from src.skills.canvas_automation import canvas_automation_skill
from src.routers.tools import router as tools_router
import os
import httpx
from pathlib import Path
import re

# Initialize Core Skills for Chat Context
workspace_skill = FileSystemSkill(DEFAULT_STORAGE_ROOT)

def require_auth(request: Request = None, websocket: WebSocket = None):
    api_key = os.environ.get("AGENT_API_KEY", "")
    if not api_key:
        return  # auth disabled if no key configured
    
    conn = request if request is not None else websocket
    auth = conn.headers.get("Authorization")
    if not auth or auth != f"Bearer {api_key}":
        raise HTTPException(status_code=401, detail="Unauthorized")

app = FastAPI(title="AI Agent Platform API", dependencies=[Depends(require_auth)])

# Define project data paths
DATA_DIR = Path("data")
SESSIONS_DIR = DATA_DIR / "sessions"
CONFIG_FILE = DATA_DIR / "config.json"

SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

# Runtime Config Management
class AppConfig(BaseModel):
    llm_url: str = LLM_BASE_URL
    default_model: str = DEFAULT_MODEL
    searxng_url: str = SEARXNG_URL
    qdrant_url: str = QDRANT_URL
    postgres_url: str = POSTGRES_URL

def load_runtime_config():
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                return AppConfig(**data)
        except Exception as e:
            logger.error(f"Failed to load runtime config: {e}")
    return AppConfig()

def save_runtime_config(config: AppConfig):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config.dict(), f, indent=4)
    except Exception as e:
        logger.error(f"Failed to save runtime config: {e}")

runtime_config = load_runtime_config()

# Enable CORS for local frontend development (allow all origins for LAN access)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Routers
app.include_router(tools_router)

class RunRequest(BaseModel):
    prompt: str
    target_node: Optional[str] = "Observer"

# In-memory storage for active graph runs
active_runs = {}

# Global event queue for streaming state updates
update_queue = asyncio.Queue()

OLLAMA_BASE = "http://localhost:11434"

class ChatRequest(BaseModel):
    prompt: str
    history: Optional[List[dict]] = []

from fastapi.responses import StreamingResponse

@app.post("/chat")
async def chat_with_ollama(request: ChatRequest):
    """Send a message to Ollama and stream the assistant's reply."""
    model = runtime_config.default_model or DEFAULT_MODEL
    logger.info(f"Starting chat with model: {model}")

    # Discover local context
    files = []
    try:
        files = [f.name for f in DEFAULT_STORAGE_ROOT.iterdir() if f.is_file()][:10]
    except:
        pass

    # Consolidated Swarm Context (Prompt Bloat Optimization)
    swarm_info = (
        f"WORKSPACE: {DEFAULT_STORAGE_ROOT} ({', '.join(files) if files else 'Empty'})\n"
        "SKILLS: Memory, WebSearch, Gmail, Office365, Docker, SkillForge, CanvasAutomation, MCP(FileSystem, Thinking)\n"
        "CANVAS: Multi-mode (Whiteboard, Markdown, Code, Preview, Document)"
    )

    messages = [
        {
            "role": "system",
            "content": (
                "You are GUIDE, a concise AI navigator. The Flute Path is your philosophy.\n\n"
                f"{swarm_info}\n\n"
                "RULES:\n"
                "1. Always identify as GUIDE.\n"
                "2. You have direct access to the files and skills listed above.\n"
                "3. Use MARKDOWN for all responses. **CRITICAL: Always use Markdown TABLES to present multiple options, structured actions, or system status.**\n"
                "4. When generating docs or code, you may use CanvasAutomation to push content to the Research Canvas directly. Suggest 'PUSH TO CANVAS' button otherwise.\n"
                "5. Be forthright. If a task is outside your current toolkit, say so."
            )
        }
    ]
    for h in (request.history or []):
        messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
    messages.append({"role": "user", "content": request.prompt})

    async def generate():
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream(
                    "POST",
                    f"{OLLAMA_BASE}/api/chat",
                    json={
                        "model": model, 
                        "messages": messages, 
                        "stream": True,
                        "options": {
                            "num_ctx": 8192,
                            "temperature": 0.7
                        }
                    }
                ) as response:
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        chunk = json.loads(line)
                        if "message" in chunk:
                            content = chunk["message"].get("content", "")
                            if content:
                                yield f"data: {json.dumps({'content': content})}\n\n"
                        if chunk.get("done"):
                            break
        except Exception as e:
            logger.error(f"Ollama streaming error: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

@app.get("/config")
async def get_config():
    return runtime_config

@app.post("/config")
async def update_config(config: AppConfig):
    global runtime_config
    runtime_config = config
    save_runtime_config(config)
    return {"status": "success", "config": runtime_config}

@app.get("/ollama/models")
async def get_ollama_models():
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{OLLAMA_BASE}/api/tags")
            resp.raise_for_status()
            data = resp.json()
            models = [m["name"] for m in data.get("models", [])]
            return {"status": "success", "models": models}
    except Exception as e:
        logger.error(f"Failed to fetch Ollama models: {e}")
        return {"status": "error", "message": str(e)}


@app.post("/run")
async def run_graph(request: RunRequest):
    """Initiates a graph execution and returns a run ID."""
    run_id = f"run_{len(active_runs) + 1}"
    
    # Initialize state
    initial_state = AgentState(current_node=request.target_node)
    initial_state.add_message("user", request.prompt)
    
    active_runs[run_id] = {"state": initial_state, "status": "running"}
    
    # Trigger graph in a background task
    asyncio.create_task(execute_graph_task(run_id, initial_state))
    
    return {"run_id": run_id, "status": "started"}

async def execute_graph_task(run_id: str, state: AgentState):
    """Bridge function to run the graph and queue updates."""
    orchestrator = StateGraphOrchestrator()
    
    # Simulate node-by-node execution for the stream
    # In a real app, we'd add hooks to the orchestrator nodes
    nodes = ["Observer", "Researcher", "Analyst", "Writer"]
    
    try:
        for node in nodes:
            if state_manager.is_halted():
                break
                
            active_runs[run_id]["state"].current_node = node
            await update_queue.put({
                "type": "state_update", 
                "run_id": run_id, 
                "node": node, 
                "status": "active"
            })
            
            # Simulate work
            await asyncio.sleep(2)
            
        active_runs[run_id]["status"] = "complete"
        await update_queue.put({"type": "run_complete", "run_id": run_id})
        
    except Exception as e:
        logger.error(f"Graph execution failed: {e}")
        active_runs[run_id]["status"] = "error"
        await update_queue.put({"type": "run_error", "run_id": run_id, "error": str(e)})

from src.utils.storage_mapper import storage_mapper
from src.skills.vision import vision_skill

@app.get("/status/{run_id}")
async def get_status(run_id: str):
    if run_id not in active_runs:
        return {"error": "Run not found"}
    return {
        "status": active_runs[run_id]["status"],
        "node": active_runs[run_id]["state"].current_node
    }

@app.post("/kill")
async def kill_all():
    state_manager.trigger_halt("API Request")
    return {"status": "halted"}

@app.post("/storage/init")
async def init_storage(path: str):
    """Phase 8: Initialize standard AI directory structure."""
    if storage_mapper.set_root(path):
        success = storage_mapper.initialize_schema()
        return {"status": "success" if success else "error"}
    return {"status": "path_not_found"}

@app.post("/vision/screenshot")
async def capture_screen(confirm: bool = False, filename: Optional[str] = None):
    """Refined Privacy: Capture first, scan, then ask if private."""
    result = vision_skill.take_screenshot(filename=filename)
    
    if not result:
        return {"status": "error", "message": "Capture failed"}

    # If it's clean and we don't need manual confirmation, finalize now
    if not result["is_sensitive"] and confirm:
        path = vision_skill.finalize_capture(result["filename"])
        return {"status": "success", "path": path}
    
    # If sensitive or we want forced review, return for auth
    return {
        "status": "requires_auth",
        "is_sensitive": result["is_sensitive"],
        "preview": result["preview"],
        "filename": result["filename"]
    }

@app.post("/vision/confirm")
async def confirm_capture(filename: str):
    """Finalize a buffered capture after user authorization."""
    path = vision_skill.finalize_capture(filename)
    if path:
        return {"status": "success", "path": path}
    return {"status": "error", "message": "Buffer not found or expired"}

@app.post("/vision/webcam")
async def capture_camera(confirm: bool = False):
    """Phase 9: Webcam Capture with Privacy Gate."""
    if not confirm:
        return {"status": "privacy_confirmation_required"}
        
    path = vision_skill.capture_webcam()
    return {"status": "success", "path": path}

@app.get("/help/snippets")
async def get_help_snippet(topic: str):
    """Phase 7: Contextual Help Snippets."""
    # Mocking contextual lookup for prototype
    help_data = {
        "graph": "The Graph View shows your agent's thinking logic in real-time.",
        "canvas": "The Infinite Canvas is for visual brainstorming.",
        "settings": "Configure your AI Storage and connection strings here."
    }
    return {"text": help_data.get(topic, "Help snippet not found.")}

@app.get("/swarm/local_status")
async def get_local_swarm_status():
    """Telemetry: Get local node resource stats."""
    return await swarm_telemetry.get_local_stats()

@app.get("/swarm/status")
async def get_global_swarm_status():
    """Telemetry: Aggregated stats from the entire Tailnet swarm."""
    return await swarm_telemetry.get_swarm_status()

# Swarm Soul Management
@app.get("/swarm/experts")
async def list_swarm_experts():
    """Lists all available expert names."""
    from src.agents.persona_loader import persona_loader
    return {"experts": persona_loader.list_experts()}

@app.get("/swarm/expert/{name}")
async def get_expert_soul(name: str):
    """Returns the raw Markdown soul of an agent."""
    from src.agents.persona_loader import persona_loader
    file_path = persona_loader.agents_dir / f"{name}.md"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Expert not found")
    with open(file_path, "r", encoding="utf-8") as f:
        return {"name": name, "soul": f.read()}

@app.post("/swarm/expert/{name}")
async def update_expert_soul(name: str, request: Request):
    """Updates the Markdown soul of an agent."""
    body = await request.json()
    soul_content = body.get("soul")
    if not soul_content:
        raise HTTPException(status_code=400, detail="Missing soul content")
    
    from src.agents.persona_loader import persona_loader
    file_path = persona_loader.agents_dir / f"{name}.md"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(soul_content)
    
    return {"status": "success", "message": f"Soul for {name} updated."}

@app.post("/swarm/expert/spawn")
async def spawn_expert(request: Request):
    """Creates a new agent from a template."""
    body = await request.json()
    name = body.get("name", "NewAgent").capitalize()
    role = body.get("role", "Specialist")
    
    from src.agents.persona_loader import persona_loader
    file_path = persona_loader.agents_dir / f"{name}.md"
    if file_path.exists():
        raise HTTPException(status_code=400, detail="Agent already exists")
    
    template = f"""---
name: {name}
engine: qwen2.5-32b-instruct
---

# Role
{role}

# Guidelines
- Be concise.
- Follow the Flute Path logic.

# Skills
- None yet.

# Evolutionary Memory
- No entries.
"""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(template)
    
    return {"status": "success", "name": name}

@app.delete("/swarm/expert/{name}")
async def delete_swarm_expert(name: str):
    """Removes an agent's Markdown soul file."""
    from src.agents.persona_loader import persona_loader
    file_path = persona_loader.agents_dir / f"{name}.md"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Expert not found")
    
    file_path.unlink()
    return {"status": "success", "message": f"Expert {name} has been dissolved."}

# Session Management Endpoints
@app.get("/sessions")
async def list_sessions():
    """Returns a list of all saved sessions with metadata."""
    files = list(SESSIONS_DIR.glob("*.json"))
    sessions = []
    for f in files:
        try:
            with open(f, "r") as sf:
                data = json.load(sf)
                sessions.append({
                    "id": data.get("id"),
                    "title": data.get("title", data.get("id")),
                    "created_at": data.get("created_at"),
                    "last_updated": data.get("last_updated", data.get("created_at"))
                })
        except Exception as e:
            logger.error(f"Error reading session {f}: {e}")
    
    # Sort by last_updated descending
    sessions.sort(key=lambda x: x["last_updated"], reverse=True)
    return {"sessions": sessions}

@app.post("/sessions/new")
async def start_new_session(name: Optional[str] = None):
    """Initializes a new session."""
    session_id = name or f"session_{int(time.time())}"
    file_path = SESSIONS_DIR / f"{session_id}.json"
    
    initial_data = {
        "id": session_id,
        "created_at": time.time(),
        "messages": []
    }
    
    with open(file_path, "w") as f:
        json.dump(initial_data, f)
        
    return {"session_id": session_id, "status": "created"}

async def generate_title(prompt: str):
    """Uses Ollama to generate a short, descriptive title based on context."""
    try:
        model = runtime_config.default_model or DEFAULT_MODEL
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{OLLAMA_BASE}/api/generate",
                json={
                    "model": model,
                    "prompt": f"Generate a short 3-5 word title for a conversation starting with: '{prompt}'. Return ONLY the title text.",
                    "stream": False
                }
            )
            title = resp.json().get("response", "New Session").strip()
            # Clean off any quotes or common prefixes
            title = title.replace('"', '').replace("'", "").replace("Title:", "").strip()
            return title
    except Exception as e:
        logger.error(f"Title generation failed: {e}")
        return "New Session"

def sanitize_id(title: str):
    """Converts a title into a filesystem-safe ID."""
    s = title.lower()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[-\s]+', '_', s)
    return s.strip('_')[:50]

@app.get("/sessions/{session_id}")
async def load_session(session_id: str):
    """Loads history for a specific session."""
    file_path = SESSIONS_DIR / f"{session_id}.json"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Session not found")
    
    with open(file_path, "r") as f:
        return json.load(f)

@app.post("/sessions/{session_id}/message")
async def add_message_to_session(session_id: str, request: Request):
    """Appends a message to the session history."""
    body = await request.json()
    role = body.get("role")
    content = body.get("content")
    
    file_path = SESSIONS_DIR / f"{session_id}.json"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Session not found")
        
    try:
        new_session_id = session_id
        
        with open(file_path, "r") as f:
            data = json.load(f)
            
        data["messages"].append({"role": role, "content": content})
        data["last_updated"] = time.time()
        
        # Auto-titling & Renaming: if no title and this is the first user message
        if not data.get("title") and role == "user":
            title = await generate_title(content)
            data["title"] = title
            
            # User wants Session ID to take on the name of the conversation
            new_session_id = sanitize_id(title)
            data["id"] = new_session_id
            
            # Rename File
            new_file_path = SESSIONS_DIR / f"{new_session_id}.json"
            
            # If target exists, append timestamp to avoid collision
            if new_file_path.exists() and new_session_id != session_id:
                new_session_id = f"{new_session_id}_{int(time.time())}"
                new_file_path = SESSIONS_DIR / f"{new_session_id}.json"
                data["id"] = new_session_id

            # Save to new location and remove old one
            with open(new_file_path, "w") as f:
                json.dump(data, f, indent=4)
            
            if file_path != new_file_path:
                file_path.unlink()
        else:
            # Normal append
            with open(file_path, "w") as f:
                json.dump(data, f, indent=4)
                
        return {"status": "success", "session_id": new_session_id}
    except Exception as e:
        logger.error(f"Failed to update session: {e}")
        raise HTTPException(status_code=500, detail="Persistence failure")

# Dynamic Configuration Endpoints
@app.get("/config")
async def get_config():
    """Returns the current runtime configuration."""
    return runtime_config

@app.post("/config")
async def update_config(config: AppConfig):
    """Updates and persists the runtime configuration."""
    global runtime_config
    runtime_config = config
    save_runtime_config(config)
    return {"status": "updated", "config": runtime_config}

@app.get("/ollama/models")
async def get_ollama_models():
    """Fetches the list of locally downloaded models from the local Ollama instance."""
    try:
        # Assuming Ollama is running on localhost:11434 as per standard
        ollama_url = runtime_config.llm_url.replace("/v1", "") if "/v1" in runtime_config.llm_url else "http://localhost:11434"
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{ollama_url}/api/tags")
            if resp.status_code == 200:
                data = resp.json()
                models = [model.get("name") for model in data.get("models", [])]
                return {"status": "success", "models": models}
            return {"status": "error", "message": f"Ollama returned {resp.status_code}"}
    except Exception as e:
        return {"status": "error", "message": f"Could not connect to Ollama: {str(e)}"}

@app.get("/search")
async def run_web_search(q: str, limit: int = 5):
    """Web Research: Multi-Tier Source Ranking + Geo-Bias."""
    return await web_search.search(q, limit)

@app.get("/browser/scrape")
async def scrape_web_page(url: str):
    """Browser Proxy: Reader-Mode text extraction."""
    return await browser_proxy.scrape_page(url)

@app.post("/browser/summarize")
async def summarize_research(request: Request):
    """AI Digest: Summary of scraped content using Qwen 32B."""
    body = await request.json()
    content = body.get("content", "")
    query = body.get("query", "")
    
    prompt = f"Summarize the following research for the query: '{query}'\n\nContent: {content[:8000]}\n\nSummary:"
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                runtime_config.llm_url + "/completions",
                json={
                    "model": runtime_config.default_model,
                    "prompt": prompt,
                    "max_tokens": 500,
                    "temperature": 0.3
                }
            )
            data = resp.json()
            return {"summary": data["choices"][0]["text"]}
    except Exception as e:
        logger.error(f"Summarization Error: {e}")
        return {"summary": "Failed to generate AI digest."}

@app.post("/forge/interview")
async def forge_interview(request: Request):
    """Guided Skill Creator: Back-and-forth interview with the SkillBuilderAgent."""
    body = await request.json()
    prompt = body.get("prompt")
    history = body.get("history", [])
    current_preview = body.get("current_preview", {})
    
    result = await skill_builder.interview_step(prompt, history, current_preview)
    return result

@app.post("/forge/assemble")
async def forge_assemble(request: Request):
    """Automated Assembly: Write finalized skill to the sandbox."""
    body = await request.json()
    preview = body.get("preview", {})
    
    skill_name = preview.get("name", "untitled_skill").lower().replace(" ", "_")
    skill_type = preview.get("type", "Skill")
    architecture = preview.get("architecture", "")
    
    sandbox_path = os.path.abspath("sandbox")
    os.makedirs(sandbox_path, exist_ok=True)
    
    file_path = os.path.join(sandbox_path, f"{skill_name}.py")
    
    with open(file_path, "w") as f:
        f.write(f"\"\"\"\nGenerated by The Skill Forge\nType: {skill_type}\n\"\"\"\n\n")
        f.write(architecture)
        
    return {"message": f"Skill forged and saved to {file_path}. Please review and test before promotion.", "path": file_path}

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10MB

@app.post("/stt")
async def speech_to_text(request: Request):
    """Voice In: Transcription using Whisper Turbo."""
    audio_data = await request.body()
    if len(audio_data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Payload too large")
    # Temporarily save bytes to file for Whisper
    temp_path = "temp_audio.wav"
    with open(temp_path, "wb") as f:
        f.write(audio_data)
    
    text = voice_stt.transcribe(temp_path)
    if os.path.exists(temp_path):
        os.remove(temp_path)
    return {"text": text}

@app.get("/tts")
async def text_to_speech(text: str):
    """Voice Out: Speech Synthesis using Kokoro-82M."""
    audio_bytes = voice_tts.speak(text)
    return {"status": "success", "audio_len": len(audio_bytes)}

@app.websocket("/stream")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        # Send initial heartbeat
        await websocket.send_text(json.dumps({
            "type": "heartbeat", 
            "halted": state_manager.is_halted()
        }))
        
        while True:
            # Wait for updates from the queue and broadcast
            update = await update_queue.get()
            await websocket.send_text(json.dumps(update))
            
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")

@app.post("/canvas/event")
async def broadcast_canvas_event(request: Request):
    """Internal endpoint for skills to push canvas events to the frontend."""
    try:
        data = await request.json()
        await update_queue.put(data)
        return {"status": "broadcast_queued"}
    except Exception as e:
        logger.error(f"Failed to queue canvas broadcast: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
