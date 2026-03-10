import asyncio
from src.core.orchestrator import StateGraphOrchestrator
from src.core.state_schema import AgentState
from src.memory.storage import MemoryLane, MemoryEntry
from src.utils.logger import logger

async def test_guide_integration():
    print("--- Testing GUIDE 5-Lane Integration ---")
    
    # 1. Setup Orchestrator
    orchestrator = StateGraphOrchestrator(agent_id="guide_test_agent")
    manager = orchestrator.memory_manager
    manager.clear() # Start fresh
    
    # 2. Seed Memory Lanes (GUIDE Section 3)
    # Add Semantic Memory (Durable Facts)
    manager.add_message(
        "system", 
        "User prefers Python for data science and JavaScript for web.", 
        lane=MemoryLane.SEMANTIC
    )
    
    # Add Working Memory (Task State)
    manager.add_message(
        "system", 
        "Currently analyzing the GUIDE architecture document.", 
        lane=MemoryLane.WORKING
    )
    
    # Add Resume Memory (Interruption)
    # This will be triggered at the start of run_graph
    manager.add_message(
        "user", 
        "Resume the previous architecture review.", 
        lane=MemoryLane.RESUME
    )
    
    # 3. Define a simple node that checks the context packet
    async def node_check_context(state: AgentState) -> AgentState:
        print("[Node] Manually invoking Memory Broker...")
        # Use a request that triggers semantic/episodic retrieval
        request = "What are my preferences?"
        
        # Manually assemble via broker for testing
        state.context_packet = orchestrator.memory_broker.assemble_context_packet(
            request, orchestrator.memory_manager.memory
        )
        
        print(f"[Node] Checking assembled context packet...")
        packet_content = [m["content"] for m in state.context_packet]
        
        # Verify Semantic Memory is present (e.g., "[KNOWLEDGE]: User prefers Python...")
        has_semantic = any("[KNOWLEDGE]" in c and "User prefers Python" in c for c in packet_content)
        # Verify Working Memory is present (e.g., "[WORKING]: Currently analyzing...")
        has_working = any("[WORKING]" in c and "Currently analyzing" in c for c in packet_content)
        # Verify System Prompt is present
        has_system = any(orchestrator.system_prompt in c for c in packet_content)
        
        if has_semantic and has_working and has_system:
            print("✅ SUCCESS: Context packet contains all expected lanes.")
            state.variables["verified"] = True
        else:
            print("❌ FAILURE: Context packet missing expected lanes.")
            print(f"Packet: {packet_content}")
            state.variables["verified"] = False
            
        return state

    orchestrator.add_node("VerifyContext", node_check_context)
    orchestrator.add_edge("VerifyContext", "END")

    # 4. Run the Graph
    # The Orchestrator should detect Resume Memory and re-entry
    initial_state = AgentState(current_node="VerifyContext")
    
    print("\nRunning Graph...")
    final_state = await orchestrator.run_graph(initial_state)
    
    if final_state.error:
        print(f"Graph Failed: {final_state.error}")
    else:
        print(f"Graph Succeeded! Verified: {final_state.variables.get('verified')}")
        
    # Verify Resume was cleared
    assert manager.memory.resume is None
    print("✅ SUCCESS: Resume memory cleared after re-entry.")

if __name__ == "__main__":
    asyncio.run(test_guide_integration())
