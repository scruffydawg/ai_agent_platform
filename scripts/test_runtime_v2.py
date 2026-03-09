import asyncio
import sys
import os
import json
from pathlib import Path

# Add project root to sys.path
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

from packages.services.runtime_service import runtime_service
from packages.services.event_service import event_service
from packages.services.approval_service import approval_service

async def test_runtime_flow():
    print("🚀 Starting Runtime V2 Integration Test...", flush=True)
    
    # 1. Define a test graph
    test_graph = {
        "id": "test_graph_1",
        "nodes": [
            {"id": "node_1", "tool": "search"}, 
            {"id": "node_2", "tool": "read_file", "requires_approval": True}
        ],
        "edges": [
            {"source": "node_1", "target": "node_2"}
        ]
    }
    
    # 2. Subscribe to events to verify telemetry
    events_received = []
    async def log_event(event):
        events_received.append(event)
        print(f"📡 Event: {event.get('type')} - {event.get('status') or event.get('event')}", flush=True)
        
    event_service.subscribe(log_event)
    
    # 3. Start graph execution
    print("▶️ Starting graph execution...", flush=True)
    try:
        exec_id = await runtime_service.run_graph(test_graph, {"query": "V2 Architecture"})
        print(f"✅ Graph execution started: {exec_id}", flush=True)
    except Exception as e:
        print(f"❌ Error starting graph: {e}", flush=True)
        return
    
    # 4. Wait for approval request
    print("⏳ Waiting for approval request...")
    req_id = None
    for _ in range(10):
        reqs = await approval_service.get_requests()
        if reqs:
            req_id = reqs[0]["id"]
            print(f"✅ Approval request found: {req_id}")
            break
        await asyncio.sleep(1)
        
    if not req_id:
        print("❌ Error: Approval request not found!")
        return

    # 5. Approve the request
    print("👍 Approving request...")
    await approval_service.decide(req_id, approved=True)
    
    # 6. Wait for completion
    print("⏳ Waiting for graph completion...")
    for _ in range(10):
        status = runtime_service.get_status(exec_id)
        if status and status.get("status") == "completed":
            print("🏁 Graph execution completed!")
            break
        await asyncio.sleep(1)
    
    # 7. Final Verification
    print("\n📊 Test Results:")
    print(f"Events received: {len(events_received)}")
    if len(events_received) >= 5: # started, node_1 started, node_1 comp, node_2 started, node_2 comp, completed
        print("✅ Events verified!")
    else:
        print("⚠️ Event count mismatch.")
        
    print("✅ Test Finished.")

if __name__ == "__main__":
    asyncio.run(test_runtime_flow())
