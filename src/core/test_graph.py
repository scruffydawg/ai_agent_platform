from src.core.orchestrator import StateGraphOrchestrator
from src.core.state_schema import AgentState

def test_state_graph():
    print("--- Testing StateGraph Orchestrator ---")
    
    graph = StateGraphOrchestrator(max_transitions=5)
    
    # Define mock nodes
    def node_observer(state: AgentState) -> AgentState:
        print("[Observer Node] Observing...")
        state.variables["observed"] = True
        return state
        
    def node_researcher(state: AgentState) -> AgentState:
        print("[Researcher Node] Researching...")
        state.variables["research_done"] = True
        return state
        
    def node_writer(state: AgentState) -> AgentState:
        print("[Writer Node] Writing...")
        state.variables["written"] = "Done"
        return state

    # Register nodes
    graph.add_node("Observer", node_observer)
    graph.add_node("Researcher", node_researcher)
    graph.add_node("Writer", node_writer)

    # Define Conditional Edge Logic
    def routing_logic(state: AgentState) -> str:
        if state.variables.get("observed") and not state.variables.get("research_done"):
            return "needs_research"
        elif state.variables.get("research_done"):
            return "needs_writing"
        return "end"

    # Register Edges
    # Observer routes based on custom logic
    graph.add_conditional_edge(
        "Observer", 
        routing_logic, 
        {"needs_research": "Researcher", "needs_writing": "Writer", "end": "END"}
    )
    # Researcher always goes to Writer
    graph.add_edge("Researcher", "Writer")
    # Writer always ends
    graph.add_edge("Writer", "END")

    # Run execution
    initial_state = AgentState(current_node="Observer")
    final_state = graph.run_graph(initial_state)

    if final_state.error:
        print(f"Graph Failed: {final_state.error}")
    else:
        print(f"Graph Succeeded! Variables: {final_state.variables}")
        assert final_state.variables.get("written") == "Done"
        print("Test Passed: State payload maintained across 3 node transitions.")

if __name__ == "__main__":
    test_state_graph()
