from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import re
import ast
import json
import subprocess
from pathlib import Path

from src.config import DEFAULT_STORAGE_ROOT
from apps.api.response_models import SuccessResponse

router = APIRouter(prefix="/tools", tags=["tools"])


# ── Data Models ──────────────────────────────────────────────────────────────

class DocsLink(BaseModel):
    label: str
    url: str


class SampleCall(BaseModel):
    action: str
    endpoint: str
    notes: str = ""


class McpServerRef(BaseModel):
    """A reference to an MCP server used by a skill."""
    name: str
    path: str = ""
    source_url: str = ""
    env_vars: List[str] = []


class CodeToolRef(BaseModel):
    """A code tool or Python library used by a skill."""
    name: str
    version: str = ""
    purpose: str = ""


class ToolCapability(BaseModel):
    """
    Unified representation of a Skill.
    Every .py in src/skills/ is a Skill. MCP servers and code tools are
    sections within the skill — not separate entities.
    """
    name: str
    description: str
    archetype: str = "skill"        # "skill" | "mcp" | "hybrid"
    type: str = "Skill"             # "Skill" | "MCP Server" (for tab filtering)
    subtype: str = "skill"          # legacy compat
    status: str = "Active"
    icon: str = "tool"
    filename: str = ""
    docs_links: List[DocsLink] = []
    mcp_servers: List[McpServerRef] = []   # MCP servers this skill uses
    code_tools: List[CodeToolRef] = []     # Python libs / execution nodes
    sample_calls: List[SampleCall] = []
    # Legacy flat fields (still usable for quick access)
    mcp_path: str = ""
    mcp_source_url: str = ""
    mcp_env_vars: List[str] = []


# ── Header Comment Parser ─────────────────────────────────────────────────────

def parse_skill_header(source: str) -> Dict[str, Any]:
    """
    Parses the standardized skill file header comment block.
    
    Expected format:
    # ============================================================
    # SKILL: N8N Workflow Automation
    # ARCHETYPE: hybrid
    # ============================================================
    # MCP_SERVERS:
    #   - name: n8n-mcp
    #     path: ~/gemini_workspace/mcp_servers/n8n-mcp
    #     source_url: https://github.com/czlonkowski/n8n-mcp
    #     env_vars: N8N_API_URL, N8N_API_KEY
    # CODE_TOOLS:
    #   - httpx==0.27 (REST calls to n8n API)
    # DOCS:
    #   - https://docs.n8n.io/api/
    # ============================================================
    """
    result: Dict[str, Any] = {
        "skill_name": None,
        "archetype": "skill",
        "mcp_servers": [],
        "code_tools": [],
        "docs": [],
    }
    
    lines = source.splitlines()
    in_block = False
    current_section = None
    current_mcp = {}
    
    for line in lines:
        stripped = line.strip()
        if not stripped.startswith("#"):
            if in_block:
                break  # Header block ended
            if stripped and not stripped.startswith("#"):
                if not in_block:
                    continue
            continue
        
        content = stripped.lstrip("#").strip()
        
        if "============" in content:
            in_block = True
            continue
        
        if content.startswith("SKILL:"):
            result["skill_name"] = content[6:].strip()
        elif content.startswith("ARCHETYPE:"):
            result["archetype"] = content[10:].strip().lower()
        elif content.startswith("MCP_SERVERS:"):
            current_section = "mcp"
            if current_mcp:
                result["mcp_servers"].append(current_mcp)
                current_mcp = {}
        elif content.startswith("CODE_TOOLS:"):
            current_section = "code"
            if current_mcp:
                result["mcp_servers"].append(current_mcp)
                current_mcp = {}
        elif content.startswith("DOCS:"):
            current_section = "docs"
            if current_mcp:
                result["mcp_servers"].append(current_mcp)
                current_mcp = {}
        elif content.startswith("- ") or content.startswith("-"):
            entry = content.lstrip("- ").strip()
            if current_section == "mcp":
                if entry.startswith("name:"):
                    if current_mcp:
                        result["mcp_servers"].append(current_mcp)
                    current_mcp = {"name": entry[5:].strip()}
                elif entry.startswith("path:") and current_mcp:
                    current_mcp["path"] = entry[5:].strip()
                elif entry.startswith("source_url:") and current_mcp:
                    current_mcp["source_url"] = entry[11:].strip()
                elif entry.startswith("env_vars:") and current_mcp:
                    current_mcp["env_vars"] = [v.strip() for v in entry[9:].split(",")]
                elif entry.startswith("name:") and not current_mcp:
                    current_mcp = {"name": entry[5:].strip()}
            elif current_section == "code":
                # Format: "httpx==0.27 (REST calls)"
                m = re.match(r"([^\s(]+)\s*(?:==([^\s(]+))?\s*(?:\((.+)\))?", entry)
                if m:
                    result["code_tools"].append({
                        "name": m.group(1),
                        "version": m.group(2) or "",
                        "purpose": m.group(3) or "",
                    })
            elif current_section == "docs":
                result["docs"].append(entry)
    
    if current_mcp:
        result["mcp_servers"].append(current_mcp)
    
    return result


# ── Hardcoded Skill Metadata ─────────────────────────────────────────────────

_SKILL_OVERRIDES: Dict[str, Dict] = {
    "n8n_control.py": {
        "skill_name": "n8n Workflow Automation",
        "archetype": "hybrid",
        "mcp_servers": [
            {
                "name": "n8n-mcp",
                "path": "~/gemini_workspace/mcp_servers/n8n-mcp/node_modules/.bin/n8n-mcp",
                "source_url": "https://github.com/czlonkowski/n8n-mcp",
                "env_vars": ["N8N_API_URL", "N8N_API_KEY"],
            }
        ],
        "code_tools": [
            {"name": "httpx", "version": ">=0.27", "purpose": "REST calls to n8n API"},
        ],
        "docs": [
            "https://docs.n8n.io/api/",
            "https://github.com/czlonkowski/n8n-mcp",
        ],
    }
}


# ── Static Docs Libraries ────────────────────────────────────────────────────

N8N_DOCS = [
    DocsLink(label="n8n Public API Documentation", url="https://docs.n8n.io/api/"),
    DocsLink(label="n8n Open Source Repository", url="https://github.com/n8n-io/n8n"),
    DocsLink(label="n8n-mcp GitHub (czlonkowski)", url="https://github.com/czlonkowski/n8n-mcp"),
]
VISION_DOCS = [
    DocsLink(label="Pillow (PIL) Documentation", url="https://pillow.readthedocs.io/"),
    DocsLink(label="OpenCV Python Docs", url="https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html"),
]
WEBSEARCH_DOCS = [
    DocsLink(label="SearXNG API Reference", url="https://docs.searxng.org/dev/search_api.html"),
    DocsLink(label="SearXNG GitHub", url="https://github.com/searxng/searxng"),
]
GMAIL_DOCS = [
    DocsLink(label="Gmail API Reference", url="https://developers.google.com/gmail/api/reference/rest"),
    DocsLink(label="Google Auth / OAuth2", url="https://developers.google.com/identity/protocols/oauth2"),
]
GDRIVE_DOCS = [
    DocsLink(label="Google Drive API v3", url="https://developers.google.com/drive/api/reference/rest/v3"),
]
OFFICE365_DOCS = [
    DocsLink(label="Microsoft Graph API", url="https://learn.microsoft.com/en-us/graph/overview"),
]
DOCKER_DOCS = [
    DocsLink(label="Docker Engine API", url="https://docs.docker.com/engine/api/"),
    DocsLink(label="Docker SDK for Python", url="https://docker-py.readthedocs.io/en/stable/"),
]
VOICE_DOCS = [
    DocsLink(label="Whisper Model (OpenAI)", url="https://platform.openai.com/docs/guides/speech-to-text"),
    DocsLink(label="pyttsx3 Docs", url="https://pyttsx3.readthedocs.io/en/latest/"),
]
MCP_SEQUENTIAL_DOCS = [
    DocsLink(label="MCP Sequential Thinking Server", url="https://github.com/modelcontextprotocol/servers/tree/main/src/sequentialthinking"),
    DocsLink(label="Anthropic MCP Spec", url="https://modelcontextprotocol.io/introduction"),
]
MCP_FILESYSTEM_DOCS = [
    DocsLink(label="MCP Filesystem Server", url="https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem"),
]

N8N_SAMPLE_CALLS = [
    SampleCall(action="List Workflows", endpoint="GET /workflows", notes="Returns all workflows with id, name, active status"),
    SampleCall(action="Get Workflow", endpoint="GET /workflows/{id}", notes="Full workflow definition including nodes and connections"),
    SampleCall(action="Trigger Webhook", endpoint="POST /webhooks/{path}", notes="Fires a webhook-triggered workflow"),
    SampleCall(action="Get Executions", endpoint="GET /executions", notes="Query params: workflowId, status, limit"),
]


# ── Registry Scan ────────────────────────────────────────────────────────────

@router.get("/registry", response_model=SuccessResponse)
async def get_tool_registry():
    """Dynamically scans src/skills for available AI Agent Skill files."""
    skills_dir = Path("src/skills")
    registry: List[ToolCapability] = []

    icon_map = {
        "browser_proxy.py":    "browser",
        "docker_management.py":"docker",
        "file_system.py":      "file",
        "gmail.py":            "mail",
        "google_drive.py":     "drive",
        "n8n_control.py":      "workflow",
        "office_365.py":       "office",
        "swarm_telemetry.py":  "activity",
        "vector_memory.py":    "database",
        "vision.py":           "eye",
        "voice_in.py":         "mic",
        "voice_out.py":        "speaker",
        "web_search.py":       "globe",
        "knowledge_search.py": "library",
    }

    docs_map: Dict[str, List[DocsLink]] = {
        "n8n_control.py":      N8N_DOCS,
        "vision.py":           VISION_DOCS,
        "web_search.py":       WEBSEARCH_DOCS,
        "gmail.py":            GMAIL_DOCS,
        "google_drive.py":     GDRIVE_DOCS,
        "office_365.py":       OFFICE365_DOCS,
        "docker_management.py":DOCKER_DOCS,
        "voice_in.py":         VOICE_DOCS,
        "voice_out.py":        VOICE_DOCS,
        "knowledge_search.py": [DocsLink(label="SentenceTransformers", url="https://www.sbert.net/"), DocsLink(label="Qdrant Vector Database", url="https://qdrant.tech/")],
    }

    if skills_dir.exists():
        for file in sorted(skills_dir.glob("*.py")):
            if file.name.startswith("__") or file.name in ("base.py", "skill_indexer.py") or file.name.startswith("test_"):
                continue

            try:
                source = file.read_text(encoding="utf-8")
                tree = ast.parse(source)

                # 1. Try header comment parser
                header = parse_skill_header(source)

                # 2. Apply hardcoded overrides (fallback for files without headers yet)
                override = _SKILL_OVERRIDES.get(file.name, {})
                if override:
                    for k, v in override.items():
                        if not header.get(k):
                            header[k] = v

                # 3. Read class docstring for description
                skill_name = header.get("skill_name") or file.stem.replace("_", " ").title()
                skill_desc = "Standard platform capability."
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        doc = ast.get_docstring(node)
                        if doc:
                            skill_desc = doc.split("\n")[0].strip()
                        break

                archetype = header.get("archetype", "skill")

                # 4. Build nested MCP server refs
                mcp_refs = [
                    McpServerRef(
                        name=m.get("name", ""),
                        path=m.get("path", ""),
                        source_url=m.get("source_url", ""),
                        env_vars=m.get("env_vars", []),
                    )
                    for m in header.get("mcp_servers", [])
                ]

                # 5. Build nested code tool refs
                code_refs = [
                    CodeToolRef(
                        name=c.get("name", ""),
                        version=c.get("version", ""),
                        purpose=c.get("purpose", ""),
                    )
                    for c in header.get("code_tools", [])
                ]

                # 6. Docs links from header or static map
                docs = docs_map.get(file.name, [])
                for url in header.get("docs", []):
                    if not any(d.url == url for d in docs):
                        docs.append(DocsLink(label=url, url=url))

                # 7. Sample calls for n8n
                sc = N8N_SAMPLE_CALLS if file.name == "n8n_control.py" else []

                # 8. Legacy flat fields (for detail panel compat)
                first_mcp = mcp_refs[0] if mcp_refs else None
                mcp_path = first_mcp.path if first_mcp else ""
                mcp_src = first_mcp.source_url if first_mcp else ""

                registry.append(ToolCapability(
                    name=skill_name,
                    description=skill_desc,
                    archetype=archetype,
                    type="Skill",
                    subtype=archetype,
                    status="Active",
                    icon=icon_map.get(file.name, "tool"),
                    filename=file.name,
                    docs_links=docs,
                    mcp_servers=mcp_refs,
                    code_tools=code_refs,
                    sample_calls=sc,
                    mcp_path=mcp_path,
                    mcp_source_url=mcp_src,
                    mcp_env_vars=first_mcp.env_vars if first_mcp else [],
                ))

            except Exception as e:
                print(f"Error scanning {file.name}: {e}")
                pass

    # ── MCP Infrastructure (pure servers, not skill files) ──────────────────
    registry.append(ToolCapability(
        name="Sequential Thinking",
        description="Local MCP Server for advanced multi-step reasoning and logic decomposition.",
        archetype="mcp",
        type="MCP Server",
        subtype="mcp",
        status="Connected",
        icon="brain",
        mcp_path="npx @modelcontextprotocol/server-sequential-thinking",
        mcp_source_url="https://github.com/modelcontextprotocol/servers/tree/main/src/sequentialthinking",
        docs_links=MCP_SEQUENTIAL_DOCS,
    ))

    registry.append(ToolCapability(
        name="Filesystem Access",
        description="Standard MCP OS file integration. Read, write, list, and search the local filesystem.",
        archetype="mcp",
        type="MCP Server",
        subtype="mcp",
        status="Connected",
        icon="folder",
        mcp_path="npx @modelcontextprotocol/server-filesystem /home/scruffydawg/gemini_workspace",
        mcp_source_url="https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem",
        docs_links=MCP_FILESYSTEM_DOCS,
    ))

    # ── Write JSON Registries (Phase 9) ─────────────────────────────────────────
    try:
        registries_dir = Path(DEFAULT_STORAGE_ROOT) / "registries"
        registries_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. Skills Registry
        skills_data = [
            {
                "name": t.name,
                "description": t.description,
                "filename": t.filename,
                "archetype": t.archetype,
                "status": t.status,
                "icon": t.icon,
                "docs_links": [{"label": d.label, "url": d.url} for d in t.docs_links],
                "sample_calls": [{"action": s.action, "endpoint": s.endpoint, "notes": s.notes} for s in t.sample_calls],
                "mcp_servers": [
                    {"name": m.name, "path": m.path, "source_url": m.source_url, "env_vars": m.env_vars}
                    for m in t.mcp_servers
                ],
                "code_tools": [
                    {"name": c.name, "version": c.version, "purpose": c.purpose}
                    for c in t.code_tools
                ]
            }
            for t in registry if t.type == "Skill"
        ]
        (registries_dir / "skills_registry.json").write_text(json.dumps(skills_data, indent=2))

        # 2. MCP Registry (De-duplicated & Health Checked)
        mcp_map = {}
        for t in registry:
            if t.type == "MCP Server":
                mcp_map[t.name] = {
                    "name": t.name,
                    "path": t.mcp_path,
                    "source_url": t.mcp_source_url,
                    "env_vars": [],
                    "status": t.status
                }
        for t in registry:
            if t.type == "Skill":
                for m in t.mcp_servers:
                    if m.name not in mcp_map:
                        mcp_map[m.name] = {
                            "name": m.name,
                            "path": m.path,
                            "source_url": m.source_url,
                            "env_vars": m.env_vars,
                            "status": "Unknown"
                        }

        # Health check ping
        for name, data in mcp_map.items():
            if data["path"]:
                if "npx" in data["path"]:
                    data["status"] = "Active"
                else:
                    mcp_binary = Path(data["path"]).expanduser()
                    # Quick health check: if local binary exists, active; otherwise offline
                    if mcp_binary.exists():
                        data["status"] = "Active"
                    else:
                        data["status"] = "Offline"
            else:
                data["status"] = "Active"
                
            # Feed status back to the registry list for the UI!
            for t in registry:
                if t.name == name:
                    t.status = data["status"]

        (registries_dir / "mcp_registry.json").write_text(json.dumps(list(mcp_map.values()), indent=2))

        # 3. Code Tools Registry
        code_map = {}
        for t in registry:
            if t.type == "Skill":
                for c in t.code_tools:
                    if c.name not in code_map:
                        code_map[c.name] = {
                            "name": c.name,
                            "version": c.version,
                            "purpose": c.purpose,
                            "used_by": [t.name]
                        }
                    else:
                        if t.name not in code_map[c.name]["used_by"]:
                            code_map[c.name]["used_by"].append(t.name)
        
        (registries_dir / "code_tools_registry.json").write_text(json.dumps(list(code_map.values()), indent=2))
            
    except Exception as e:
        print(f"Error writing JSON registries: {e}")

    return SuccessResponse(data=registry)


# ── Fetch JSON Registries (Phase 9) ──────────────────────────────────────────

@router.get("/registries/{registry_name}")
async def get_json_registry(registry_name: str):
    """Fetches a specific JSON registry (skills, mcp, code_tools)."""
    allowed = ["skills_registry.json", "mcp_registry.json", "code_tools_registry.json"]
    if f"{registry_name}_registry.json" not in allowed:
        return {"status": "error", "message": "Invalid registry expected"}
        
    filepath = Path(DEFAULT_STORAGE_ROOT) / "registries" / f"{registry_name}_registry.json"
    if not filepath.exists() or not filepath.is_file():
        # Trigger a scan to generate them if they don't exist
        await get_tool_registry()
        
    if not filepath.exists():
        return []
        
    try:
        content = filepath.read_text()
        return json.loads(content)
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ── Source Read / Write ──────────────────────────────────────────────────────

class ToolSourceUpdate(BaseModel):
    filename: str
    content: str


class ConsultMessage(BaseModel):
    role: str
    content: str


class ConsultRequest(BaseModel):
    tool_name: str
    tool_type: str
    tool_description: str
    tool_source: str
    tool_metadata: Dict[str, Any]
    messages: List[ConsultMessage]


@router.post("/registry/consult")
async def consult_guide(request: ConsultRequest):
    """Guide Contextual Consult: Provides LLM-powered insights about a tool."""
    try:
        from src.llm.client import LLMClient
        llm = LLMClient()
        
        # Build prompt
        system_prompt = f"""You are 'Guide', the platform's AI Architect. 
You are providing a contextual consult for the tool: {request.tool_name} ({request.tool_type}).
Description: {request.tool_description}
Metadata: {json.dumps(request.tool_metadata)}

The tool's source code is provided below:
---
{request.tool_source}
---

Answer the user's questions about how to use, configure, or improve this tool. 
Be concise, elite, and helpful. Use markdown.
"""
        
        messages = [{"role": "system", "content": system_prompt}]
        for m in request.messages:
            messages.append({"role": m.role, "content": m.content})
            
        response = await llm.generate_async(messages=messages)
        return {"status": "success", "response": response}
    except Exception as e:
        logger.error(f"Consult Error: {e}")
        return {"status": "error", "message": str(e)}



@router.get("/source")
async def get_tool_source(filename: str):
    """Retrieves the raw source code of a tool script."""
    filepath = Path("src/skills") / filename
    if not filepath.exists() or not filepath.is_file():
        return {"status": "error", "message": "Tool file not found."}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        return {"status": "success", "content": content}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/source")
async def update_tool_source(update: ToolSourceUpdate):
    """Updates the raw source code of a tool script."""
    filepath = Path("src/skills") / update.filename
    if not filepath.exists() or not filepath.is_file():
        return {"status": "error", "message": "Tool file not found."}
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(update.content)
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
