import sys
import threading
from src.core.orchestrator import StateGraphOrchestrator
from src.core.state_schema import AgentState
from src.core.state import state_manager
from src.core.heartbeat import heartbeat
from src.ui.cli import cli
from src.utils.logger import logger

def setup_graph():
    """Initializes the Phase 2 Graph Architecture."""
    logger.info("Initializing Agent Graph Scaffold...")
    
    # 1. Initialize StateGraph
    graph = StateGraphOrchestrator()
    
    # 2. Define specialized node functions (simulated)
    def node_researcher(state: AgentState) -> AgentState:
        cli.print_state("Researcher", "Thinking", "Researching based on user request.")
        state.add_message("assistant", "Found data about AI trends in 2026.", sender="researcher")
        state.variables["needs_formatting"] = True
        return state

    def node_coder(state: AgentState) -> AgentState:
        cli.print_state("Coder", "Acting", "Writing scaffolding code.")
        state.add_message("assistant", "Final code script drafted.", sender="coder")
        return state

    # 3. Register nodes
    graph.add_node("Researcher", node_researcher)
    graph.add_node("Coder", node_coder)

    # 4. Define Edges (Deterministic Phase 2 logic)
    # Start -> Researcher -> Coder -> END
    graph.add_edge("Researcher", "Coder")
    graph.add_edge("Coder", "END")
    
    return graph

def listen_for_kill_switch():
    """Background thread to listen for a manual kill switch (Enter key)."""
    input()
    state_manager.trigger_halt("Manual Override via Keyboard")

def main():
    cli.print_success("Platform Activated (Phase 2 Graph-Edition)")
    cli.print_state("System", "Ready", "Press ENTER at any time to trigger the Kill Switch.")
    
    # Start the kill switch listener
    kill_thread = threading.Thread(target=listen_for_kill_switch, daemon=True)
    kill_thread.start()

    # Start the Heartbeat scheduler
    heartbeat.start()
    
    graph = setup_graph()

    try:
        while not state_manager.is_halted():
            user_input = input("\n[User]: ")
            
            if user_input.lower() in ['exit', 'quit']:
                break
                
            if not user_input.strip():
                continue

            # Phase 2: Create initial state and run graph
            initial_state = AgentState(current_node="Researcher")
            initial_state.add_message("user", user_input)
            
            final_state = graph.run_graph(initial_state)
            
            if state_manager.is_halted():
                break
                
            if final_state.error:
                 cli.print_error(f"Graph Error: {final_state.error}")
            else:
                 cli.print_success("Task complete.")
            
    except KeyboardInterrupt:
        state_manager.trigger_halt("Keyboard Interrupt (Ctrl+C)")
    finally:
        logger.info("Shutting down...")
        heartbeat.stop()
        cli.print_state("System", "Halted", "Platform Shutdown Complete.")
        sys.exit(0)

if __name__ == "__main__":
    main()
