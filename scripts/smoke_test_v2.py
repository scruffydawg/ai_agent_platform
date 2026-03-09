import httpx
import asyncio
import json
import sys

BASE_URL = "http://localhost:8001/api/v2"

async def test_endpoint(client, method, path, json_data=None):
    url = f"{BASE_URL}{path}"
    print(f"🔍 Testing {method} {path}...", end="", flush=True)
    try:
        if method == "GET":
            response = await client.get(url)
        elif method == "POST":
            response = await client.post(url, json=json_data)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") in ["success", "healthy"]:
                print(" ✅ PASS", flush=True)
                return True
            else:
                print(f" ⚠️  FAIL (Logic error: {data.get('message')})", flush=True)
        else:
            print(f" ❌ FAIL (HTTP {response.status_code})", flush=True)
    except Exception as e:
        print(f" ❌ ERROR ({e})", flush=True)
    return False

async def run_smoke_test():
    print("🚀 Starting V2 API Smoke Test...")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        results = []
        
        # 1. Health
        results.append(await test_endpoint(client, "GET", "/health"))
        
        # 2. Config
        results.append(await test_endpoint(client, "GET", "/config/"))
        
        # 3. Sessions
        results.append(await test_endpoint(client, "GET", "/sessions/"))
        
        # 4. Approvals
        results.append(await test_endpoint(client, "GET", "/approvals"))
        
        # 5. Knowledge
        results.append(await test_endpoint(client, "GET", "/knowledge/search?q=test"))
        
        # 6. Forge
        results.append(await test_endpoint(client, "POST", "/forge/interview", {"prompt": "test"}))

        # 7. Tool Registry
        results.append(await test_endpoint(client, "GET", "/tools/registry"))

        success_count = sum(1 for r in results if r)
        print(f"\n📊 Summary: {success_count}/{len(results)} endpoints passed.")
        
        if success_count == len(results):
            print("✨ ALL CORE V2 ENDPOINTS VERIFIED!")
            return True
        else:
            print("❌ SOME ENDPOINTS FAILED. PLEASE CHECK LOGS.")
            return False

if __name__ == "__main__":
    # Check if server is running
    try:
        asyncio.run(run_smoke_test())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Fatal test error: {e}")
