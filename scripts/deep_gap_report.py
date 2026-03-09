import requests
import json
import importlib.util
import subprocess
import time
import ast
import os
from pathlib import Path

API_BASE = "http://localhost:8001"
OUTPUT_FILE = "/home/scruffydawg/.gemini/antigravity/brain/efdf42c0-dad0-4b7e-9eeb-e3b8e5468c03/gap_report.md"

def test_config():
    try:
        r = requests.get(f"{API_BASE}/config", timeout=5)
        return r.json()
    except:
        return {}

def test_llm(llm_url, model):
    if not llm_url or not model:
        return "Not Configured"
    try:
        r = requests.post(
            f"{llm_url.replace('/v1', '')}/api/generate",
            json={"model": model, "prompt": "test", "stream": False},
            timeout=10
        )
        if r.status_code == 200:
            return "PASS (Ollama Responds)"
        return f"FAIL (HTTP {r.status_code})"
    except Exception as e:
        return f"FAIL (Connection Error: {e})"

def test_qdrant(url):
    if not url: return "Not Configured"
    try:
        r = requests.get(url, timeout=5)
        return "PASS" if r.status_code == 200 else f"FAIL ({r.status_code})"
    except:
        return "FAIL (Connection Error)"

def test_searxng(url):
    if not url: return "Not Configured"
    try:
        r = requests.get(url, timeout=5)
        return "PASS" if r.status_code < 500 else f"FAIL ({r.status_code})"
    except:
        return "FAIL (Connection Error)"

def check_python_module(m_name):
    builtins = ["os", "sys", "json", "time", "ast", "logging", "asyncio", "pathlib", "datetime", "typing", "re", "base64", "urllib", "subprocess", "socket", "tempfile", "shutil"]
    if m_name in builtins or m_name.startswith("src.") or m_name == "src":
        return True
        
    module_mapping = {
        "docker-py": "docker",
        "google-auth": "google.auth",
        "google-auth-oauthlib": "google_auth_oauthlib",
        "google-auth-httplib2": "googleapiclient",
        "google-api-python-client": "googleapiclient",
        "beautifulsoup4": "bs4",
        "sentence-transformers": "sentence_transformers",
    }
    actual_name = module_mapping.get(m_name, m_name.replace("-", "_"))
    
    try:
        spec = importlib.util.find_spec(actual_name)
        if spec is not None:
            return True
    except:
        pass
    return False

def get_ast_imports(filepath):
    imports = set()
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])
    except Exception as e:
        pass
    return list(imports)

def generate_report():
    print("Running deep diagnostics...")
    config = test_config()
    
    lines = []
    lines.append("# Intelligent Gap & Capabilities Report")
    lines.append(f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    lines.append("## Core Services Health")
    lines.append("| Service | Configured URL | Status |")
    lines.append("|---|---|---|")
    
    llm_status = test_llm(config.get("llm_url"), config.get("default_model"))
    qdrant_status = test_qdrant(config.get("qdrant_url"))
    searxng_status = test_searxng(config.get("searxng_url"))
    
    lines.append(f"| LLM Engine ({config.get('default_model', 'N/A')}) | `{config.get('llm_url', 'N/A')}` | {llm_status} |")
    lines.append(f"| Vector DB (Qdrant) | `{config.get('qdrant_url', 'N/A')}` | {qdrant_status} |")
    lines.append(f"| Search Engine (SearXNG) | `{config.get('searxng_url', 'N/A')}` | {searxng_status} |")
    
    lines.append("\n## External Tools & Libraries")
    lines.append("| Skill / Capability | Missing Dependencies | Status |")
    lines.append("|---|---|---|")
    
    missing_capabilities = []
    
    skills_dir = Path("/home/scruffydawg/gemini_workspace/ai_agent_platform/src/skills")
    if skills_dir.exists():
        for file in sorted(skills_dir.glob("*.py")):
            if file.name.startswith("__") or file.name in ("base.py", "skill_indexer.py") or file.name.startswith("test_"):
                continue
                
            skill_name = file.stem.replace("_", " ").title()
            imports = get_ast_imports(file)
            missing_imports = []
            
            for imp in imports:
                if not check_python_module(imp):
                    missing_imports.append(imp)
            
            if missing_imports:
                lines.append(f"| {skill_name} | {', '.join(missing_imports)} | FAIL |")
                missing_capabilities.append(f"- **{skill_name}** is missing Python library `{', '.join(missing_imports)}`")
            else:
                lines.append(f"| {skill_name} | None | PASS |")
                
    lines.append("\n## Gap Analysis")
    if not missing_capabilities:
        lines.append("✅ No missing Python dependencies found for registered skills.")
    else:
        lines.append("The following system dependencies need to be addressed before certain skills will function:")
        for m in missing_capabilities:
            lines.append(m)
            
    # Hard gaps (known mocked implementations)
    lines.append("\n### Known Implementation Gaps (Mocks)")
    lines.append("- **Office 365**: Uses a mock token class instead of a real OAuth flow.")
    lines.append("- **Google Drive**: Uses a mock execution because the OAuth credentials.json is not provisioned.")
    lines.append("- **Voice In/Out**: Requires binaries (Whisper turbo, Kokoro models) to be downloaded fully to function properly outside of dummy audio buffers.")
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Deep report generated at {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_report()
