import requests
import json
import time

API_BASE = "http://localhost:8001"

def test_endpoint(path, method="GET", data=None):
    url = f"{API_BASE}{path}"
    print(f"Testing {method} {url}...")
    try:
        if method == "GET":
            r = requests.get(url, timeout=5)
        else:
            r = requests.post(url, json=data, timeout=5)
        
        print(f"Status: {r.status_code}")
        if r.status_code < 300:
            print("Response:", json.dumps(r.json(), indent=2)[:200], "...")
            return True
        else:
            print("Error:", r.text)
            return False
    except Exception as e:
        print(f"Connection failed: {e}")
        return False

def run_suite():
    print("=== V2 API SANITY SUITE ===")
    tests = [
        ("/", "GET", None),
        ("/health", "GET", None),
        ("/config/", "GET", None),
        ("/sessions/", "GET", None),
        ("/memory/guide/learnings", "GET", None),
        ("/swarm/experts", "GET", None),
    ]
    
    passed = 0
    for path, method, data in tests:
        if test_endpoint(path, method, data):
            passed += 1
            
    print(f"\nResults: {passed}/{len(tests)} passed.")

if __name__ == "__main__":
    run_suite()
