import asyncio
import sys
import os
import json
import httpx
from pathlib import Path

# Add src to path so we can import from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

API_BASE = "http://localhost:8001"

async def test_chat_tool_call():
    print("\n--- TEST: ORCHESTRATOR TOOL CALL ---")
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Prompt designed to trigger a specific tool (canvas_push)
        prompt = "Create a hello world python script in the canvas."
        print(f"Sending prompt: {prompt}")
        
        try:
            response = await client.post(
                f"{API_BASE}/chat",
                json={"prompt": prompt, "history": []}
            )
            response.raise_for_status()
            
            # The response is a stream of Server-Sent Events
            content = ""
            tool_detected = False
            for line in response.iter_lines():
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    if data.get("content"):
                        chunk = data["content"]
                        content += chunk
                        if "Executing `push_to_canvas`" in chunk:
                            tool_detected = True
            
            print(f"Resulting content summary: {content[:100]}...")
            if tool_detected:
                print("✅ PASS: Orchestrator detected and triggered the tool.")
            else:
                print("❌ FAIL: Orchestrator did not trigger the tool.")
                
        except Exception as e:
            print(f"❌ FAIL: Request failed: {e}")

async def test_skill_file_access():
    print("\n--- TEST: SKILL FILE ACCESS ---")
    # This simulates what the agent tries to do via FileSystemSkill
    from src.skills.file_system import FileSystemSkill
    from src.config import DEFAULT_STORAGE_ROOT, PROJECT_ROOT
    
    fs = FileSystemSkill({
        "workspace": DEFAULT_STORAGE_ROOT,
        "src": PROJECT_ROOT / "src"
    })
    
    # Try to read a skill file (which is now allowed via 'src' root)
    target_skill = "src/skills/browser_proxy.py"
    print(f"Attempting to read {target_skill} via authorized 'src' root")
    
    res = fs.run("read", target_skill)
    if res.get("status") == "success":
        print("✅ PASS: Successfully read skill file via authorized root.")
    else:
        print(f"❌ FAIL: {res.get('message')}")

async def test_skill_indexing():
    print("\n--- TEST: SKILL INDEXING ---")
    from src.skills.skill_indexer import skill_indexer
    import time
    
    # Search for something very likely to exist
    results = skill_indexer.search("skill")
    if results:
        print(f"✅ PASS: Found {len(results)} matches for 'browser'.")
        print(f"First match: {results[0].get('name')}")
    else:
        print("❌ FAIL: Skill Indexer returned no results.")

async def main():
    print("=== DEEP ORCHESTRATOR DIAGNOSTICS ===")
    await test_skill_indexing()
    await test_skill_file_access()
    await test_chat_tool_call()

if __name__ == "__main__":
    asyncio.run(main())
