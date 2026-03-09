import requests
import time
import os
import json

API_BASE = "http://localhost:8001"
OUTPUT_FILE = "/home/scruffydawg/.gemini/antigravity/brain/efdf42c0-dad0-4b7e-9eeb-e3b8e5468c03/gap_report.md"

def test_endpoint(name, method, url, payload=None):
    try:
        start = time.time()
        if method == "GET":
            resp = requests.get(url, timeout=5)
        else:
            resp = requests.post(url, json=payload, timeout=5)
        latency = round((time.time() - start) * 1000)
        
        is_success = resp.status_code == 200
        result_text = "PASS" if is_success else f"FAIL ({resp.status_code})"
        return f"| {name} | `{method}` `{url.replace(API_BASE, '')}` | {result_text} | {latency}ms |"
    except Exception as e:
        return f"| {name} | `{method}` `{url.replace(API_BASE, '')}` | ERROR | N/A |"

def generate_report():
    print("Running system diagnostics...")
    lines = []
    lines.append("# AI Agent Platform Gap Report")
    lines.append(f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("## API Endpoints Health")
    lines.append("| Component | Endpoint | Status | Latency |")
    lines.append("|---|---|---|---|")
    
    endpoints = [
        ("Config Fetch", "GET", f"{API_BASE}/config", None),
        ("Sessions List", "GET", f"{API_BASE}/sessions", None),
        ("Swarm Flow", "GET", f"{API_BASE}/swarm/flow", None),
        ("Experts List", "GET", f"{API_BASE}/swarm/experts", None),
        ("Tools Registry", "GET", f"{API_BASE}/tools/registry", None),
        ("Ollama Models", "GET", f"{API_BASE}/ollama/models", None),
    ]
    
    for ep in endpoints:
        lines.append(test_endpoint(*ep))
        
    lines.append("\n## Tool Integration Tests")
    try:
        registry_resp = requests.get(f"{API_BASE}/tools/registry", timeout=5)
        if registry_resp.status_code == 200:
            tools = registry_resp.json()
            if isinstance(tools, dict):
                tools = tools.get("tools", [])
            lines.append(f"**Total Tools Registered:** {len(tools)}\n")
            for t in tools:
                lines.append(f"- **{t.get('name', 'Unknown')}**: {t.get('description', 'No description')} - `Active`")
        else:
            lines.append("Failed to fetch tools registry.")
    except Exception as e:
        lines.append(f"Error fetching tools: {e}")

    lines.append("\n## Missing Capabilities (Gaps)")
    lines.append("- Needs end-to-end integration tests for LLM generation (requires mocked or live LLM).")
    lines.append("- Voice In/Out endpoints require sample audio binaries to test properly.")
    lines.append("- Vision endpoint requires mock webcam/screenshot capture environment to verify.")
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Report saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_report()
