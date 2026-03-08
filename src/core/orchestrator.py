from typing import Dict, Any, Type, Callable
from src.agents.base import BaseAgent
from src.core.state import state_manager
from src.core.state_schema import AgentState
from src.ui.cli import cli # For progress tracking updates
from src.agents.persona_loader import persona_loader
from src.utils.logger import logger

class StateGraphOrchestrator(BaseAgent):
    """
    A lightweight, deterministic StateGraph Orchestrator (Phase 2).
    Executes a predefined graph of nodes passing an AgentState payload.
    """
    def __init__(self, model: str = "gpt-4o", max_transitions: int = 20):
        super().__init__(
            agent_id="graph_orchestrator",
            system_prompt="You route states through the graph.",
            model=model
        )
        self.nodes: Dict[str, Callable[[AgentState], AgentState]] = {}
        self.edges: Dict[str, Dict[str, Any]] = {} # node -> dict of edge conditions
        self.max_transitions = max_transitions

    def add_node(self, name: str, node_func: Callable[[AgentState], AgentState]):
        """Registers a function or Agent's run method as an executable Node."""
        self.nodes[name] = node_func

    def add_edge(self, source_node: str, next_node: str):
        """Adds a direct edge between nodes."""
        if source_node not in self.edges:
             self.edges[source_node] = {}
        self.edges[source_node]['always'] = next_node

    def add_conditional_edge(self, source_node: str, condition_func: Callable[[AgentState], str], mapping: Dict[str, str]):
        """Adds an edge determined by a function that checks the current state."""
        if source_node not in self.edges:
             self.edges[source_node] = {}
        self.edges[source_node]['_conditional'] = {
             'func': condition_func,
             'mapping': mapping
        }

    async def observe_and_reason(self, state: AgentState) -> AgentState:
        # Internal node for high-level routing
        state.current_node = "reasoning"
        logger.info(f"Orchestrator reasoning. History: {len(state.messages)}")
        
        # Decide next node
        if state.variables.get("requires_review"):
             state.next_node = "moderate"
        else:
             state.next_node = "observing" # default for now
             
        return state

    async def moderate(self, state: AgentState) -> AgentState:
        """The Expert Panel Review Node."""
        state.current_node = "moderate"
        experts = ["Architect", "ADHD_UX", "Security"]
        
        for expert_name in experts:
            persona = persona_loader.load_persona(expert_name)
            if persona:
                logger.info(f"Invoking Expert Panelist: {expert_name}")
                # Mocking expert critique for prototype
                critique = f"[Critique from {expert_name}]: Plan looks solid."
                state.messages.append({"role": "system", "name": expert_name, "content": critique})
        
        state.variables["requires_review"] = False
        state.next_node = "observing"
        return state

    def run_graph(self, initial_state: AgentState) -> AgentState:
        """Executes the graph deterministically until reaching the END node or max transitions."""
        
        current_node_name = initial_state.current_node
        state = initial_state
        transitions = 0
        
        # We try to call our new Phase 2 UI hook, defaulting to pass if not built yet
        if hasattr(cli, 'start_progress'):
            cli.start_progress("Graph Execution Started") 
            
        while True:
            if transitions >= self.max_transitions:
                state.error = f"Max transitions ({self.max_transitions}) reached without reaching END node."
                break

            if state_manager.is_halted():
                state.error = "Graph halted by Kill Switch."
                break

            if current_node_name == "END" or not current_node_name:
                break

            # 1. Execute Node
            if current_node_name not in self.nodes:
                 state.error = f"Node '{current_node_name}' not defined in graph."
                 break

            if hasattr(cli, 'update_progress'):
                cli.update_progress(f"Executing Node: {current_node_name}")
            else:
                cli.print_state("Graph", "Acting", f"Node: {current_node_name}")
            
            try:
                node_func = self.nodes[current_node_name]
                state = node_func(state) # The node MUST return the modified state
                state.current_node = current_node_name
            except Exception as e:
                state.error = f"Node execution failed: {e}"
                break
                
            if state.error:
                 break

            # 2. Determine Next Edge
            next_node = "END" # Default to ending if no edge defined
            
            if current_node_name in self.edges:
                edge_logic = self.edges[current_node_name]
                
                if '_conditional' in edge_logic:
                    # Execute conditional logic
                    cond_func = edge_logic['_conditional']['func']
                    cond_mapping = edge_logic['_conditional']['mapping']
                    result_key = cond_func(state)
                    next_node = cond_mapping.get(result_key, "END")
                elif 'always' in edge_logic:
                    # Execute direct edge
                    next_node = edge_logic['always']
                    
            current_node_name = next_node
            state.next_node = next_node
            transitions += 1

        if hasattr(cli, 'stop_progress'):
            if state.error:
                 cli.stop_progress(success=False, msg=state.error)
            else:
                 cli.stop_progress(success=True, msg="Graph Execution Complete")
                 
        return state
