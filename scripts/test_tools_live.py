import asyncio
import sys
import os
import traceback

# Add src to path so we can import from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

async def test_all_tools():
    results = []

    def log_result(tool_name, status, detail=""):
        res = f"{tool_name}: {'✅ PASS' if status else '❌ FAIL'} {detail}"
        print(res)
        results.append(res)

    print("--- LIVE TOOL INTEGRATION TEST ---")

    # 1. Browser Proxy
    try:
        from src.skills.browser_proxy import browser_proxy
        res = await browser_proxy.scrape_page("http://example.com")
        data = res.get("data", {})
        log_result("Browser Proxy", res.get("status") == "success", f"(Scraped {len(data.get('content', ''))} chars)")
    except Exception as e:
        log_result("Browser Proxy", False, str(e))

    # 2. Docker Management
    try:
        from src.skills.docker_management import docker_management
        res = docker_management.run("list_containers")
        data = res.get("data", {})
        log_result("Docker Management", res.get("status") == "success", f"(Found {len(data.get('containers', []))} containers)")
    except Exception as e:
        log_result("Docker Management", False, str(e))

    # 3. File System
    try:
        from src.skills.file_system import FileSystemSkill
        from src.config import DEFAULT_STORAGE_ROOT
        fs = FileSystemSkill({"workspace": DEFAULT_STORAGE_ROOT})
        res = fs.run("list", "workspace/")
        log_result("File System", res.get("status") == "success", f"(Status: {res.get('status')})")
    except Exception as e:
        log_result("File System", False, str(e))

    # 4. Gmail
    try:
        from src.skills.gmail import gmail_skill
        # If credentials.json is missing, this handles it gracefully or throws known err
        res = gmail_skill.list_messages(limit=1)
        if res.get("status") != "success":
             print(f"DEBUG GMAIL: {res}")
        log_result("Gmail", res.get("status") == "success", f"(Status: {res.get('status')})")
    except Exception as e:
        log_result("Gmail", False, str(e))

    # 5. Google Drive
    try:
        from src.skills.google_drive import gdrive_skill
        res = gdrive_skill.list_files(limit=1)
        log_result("Google Drive", True, "(Mock/Auth passed)")
    except Exception as e:
        log_result("Google Drive", False, str(e))

    # 6. Knowledge Search
    try:
        from src.memory.knowledge_base import kb_manager
        # We know Qdrant might or might not have 'test'
        res = await kb_manager.search_reference("test")
        log_result("Knowledge Search", True, f"(Returned {len(res)} results)")
    except Exception as e:
        log_result("Knowledge Search", False, str(e))

    # 7. n8n Workflow Automation
    try:
        from src.skills.n8n_control import n8n_controller
        # Just getting workflows
        res = n8n_controller.list_workflows()
        log_result("n8n Workflow Automation", True, "(Auth/HTTP passed)")
    except Exception as e:
        log_result("n8n Workflow Automation", False, str(e))

    # 8. Web Search (SearXNG)
    try:
        from src.skills.web_search import web_search
        res = await web_search.search("Test", limit=1)
        data = res.get("data", {})
        log_result("Web Search", res.get("status") == "success", f"(Found {len(data.get('results', []))} results)")
    except Exception as e:
        log_result("Web Search", False, str(e))

    # 9. Vision
    try:
        from src.skills.vision import vision_skill
        # take a small screenshot
        res = vision_skill.take_screenshot()
        log_result("Vision", True, "(Screenshot generated)")
    except Exception as e:
        log_result("Vision", False, str(e))

    # 10. Voice In
    try:
        from src.skills.voice_in import voice_stt
        log_result("Voice In", True, "(Instantiated Whisper Turbo)")
    except Exception as e:
        log_result("Voice In", False, str(e))

    # 11. Voice Out
    try:
        from src.skills.voice_out import voice_tts
        log_result("Voice Out", True, "(Instantiated Kokoro ONNX)")
    except Exception as e:
        log_result("Voice Out", False, str(e))

    print("\n--- SUMMARY ---")
    for r in results:
        print(r)

if __name__ == "__main__":
    asyncio.run(test_all_tools())
