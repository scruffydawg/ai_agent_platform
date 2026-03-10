from typing import Dict, Any, Type, Callable
from src.agents.base import BaseAgent
from src.core.state import state_manager
from src.core.state_schema import AgentState
from src.ui.cli import cli # For progress tracking updates
from src.agents.persona_loader import persona_loader
from src.memory.manager import MemoryManager
from src.memory.broker import MemoryBroker
from src.memory.storage import MemoryLane
from src.utils.logger import logger
from pathlib import Path
from packages.services.screen_service import screen_service
from packages.services.event_service import event_service
from packages.services.queue_service import queue_service
from packages.services.metrics_service import metrics_service
import json
import asyncio
import time

class StateGraphOrchestrator(BaseAgent):
    """
    A lightweight, deterministic StateGraph Orchestrator (Phase 2).
    Executes a predefined graph of nodes passing an AgentState payload.
    """
    def __init__(self, agent_id: str = "graph_orchestrator", model: str = "gpt-4o", max_transitions: int = 20):
        super().__init__(
            agent_id=agent_id,
            system_prompt="You route states through the graph.",
            model=model
        )
        self.nodes: Dict[str, Callable[[AgentState], AgentState]] = {}
        self.edges: Dict[str, Dict[str, Any]] = {} # node -> dict of edge conditions
        self.max_transitions = max_transitions
        
        # GUIDE Memory Support
        self.memory_manager = MemoryManager(self.agent_id, self.system_prompt)
        self.memory_broker = MemoryBroker()
        
        self._load_dynamic_flow()

    def _load_dynamic_flow(self):
        """Loads the graph topology from the persisted UI flow."""
        flow_path = Path("data/swarm_flow.json")
        if not flow_path.exists():
            return

        try:
            with open(flow_path, "r") as f:
                flow = json.load(f)
            
            # Map edges
            for edge in flow.get("edges", []):
                source = edge.get("source")
                target = edge.get("target")
                if source and target:
                    self.add_edge(source, target)
                    
            # Map nodes to Expert Personas
            for node in flow.get("nodes", []):
                name = node.get("id")
                if name:
                    self.add_node(name, self._create_expert_node(name))
        except Exception as e:
            logger.error(f"Failed to load dynamic flow: {e}")

    def _create_expert_node(self, expert_name: str):
        """Standard wrapper to invoke an expert's persona logic as a graph node."""
        async def expert_node_func(state: AgentState) -> AgentState:
            persona = persona_loader.load_persona(expert_name)
            if not persona:
                 state.add_message("system", f"Expert {expert_name} persona not found.", sender=expert_name)
                 return state

            # Ensure memory is initialized
            if self.memory_manager.memory is None:
                await self.memory_manager.initialize()

            # 1. Assemble context via Memory Broker (GUIDE Stage 8)
            # We treat the last user message as the request
            last_msg = state.get_last_message()
            request = last_msg.content if last_msg else "Continue task"
            
            # Assemble the packet
            state.context_packet = await self.memory_broker.assemble_context_packet(
                request, self.memory_manager.memory
            )
            
            # 2. Update Working Memory (GUIDE Section 3.2)
            await self.memory_manager.add_message(
                "system", 
                f"Executing node: {expert_name}", 
                lane=MemoryLane.WORKING
            )
            
            # Mocking execution for now
            state.add_message("assistant", f"Processing via {expert_name}...", sender=expert_name)
            
            # Record outcome in session lane
            # 3. Dynamic UI Manifestation (Phase 4)
            # If the result seems complex, manifest it visually
            if expert_name in ["Architect", "KnowledgeHub"]:
                # ... manifestation logic ...
                pass

            # 4. Recursive Sub-Graph Support (Phase 8)
            if "RECURSIVE_SWARM" in request:
                logger.info(f"Orchestrator: Recursive swarm triggered by {expert_name}")
                sub_orchestrator = StateGraphOrchestrator(agent_id=f"sub_{expert_name}_{int(time.time())}")
                # Transfer relevant context to sub-graph
                sub_state = AgentState(variables=state.variables.copy())
                sub_state.add_message("user", state.get_last_message().content)
                
                # Execute sub-graph
                result_state = await sub_orchestrator.run_graph(sub_state)
                
                # Merge results back
                state.add_message("assistant", f"Sub-swarm result: {result_state.get_last_message().content if result_state.get_last_message() else 'No result'}", sender=f"sub_{expert_name}")
                state.variables.update(result_state.variables)

            return state
        return expert_node_func

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

    async def run_queued(self, state: AgentState, priority: int = 10) -> AgentState:
        """Admission Control: Enqueue request and wait for turn."""
        queue_size = await queue_service.get_queue_size()
        if queue_size > 100:
             state.error = "System Saturation: Queue is too long."
             return state
             
        # Enqueue state identifier (using session_id)
        session_id = state.variables.get("session_id", "default")
        await queue_service.enqueue(session_id, priority=priority)
        
        # Poll for turn (Simplified FIFO check for simulation)
        while True:
            # In a real system, a worker would pull from queue.
            # Here, the request 'waits' its turn in the orchestrator flow.
            # We'll simulate 'waiting' by checking if we are top 3.
            if await queue_service.get_queue_size() <= 3:
                break
            await asyncio.sleep(1)
            
        return await self.run_graph(state)

    async def metacognitive_observer(self, state: AgentState) -> AgentState:
        """Metacognition: Review swarm state for loops or stagnation (Phase 8)."""
        # History check for loop detection (nodes visited)
        history = [n for n in state.variables.get("node_history", []) if n != "metacognitive_observer"]
        
        # Simple loop detection: same node 3 times in a row
        if len(history) >= 3 and len(set(history[-3:])) == 1:
            logger.warning(f"Metacognitor: Loop detected in node '{history[-1]}'. Forcing redirection.")
            state.error = f"Metacognitive Redirect: Loop detected in {history[-1]}"
            state.next_node = "observing" # Back to human for intervention
            return state

        # Return to the planned path
        state.next_node = state.variables.get("planned_next_node", "END")
        return state

    async def run_graph(self, initial_state: AgentState) -> AgentState:
        """Executes the graph deterministically until reaching the END node or max transitions."""
        start_time = time.time()
        
        # Ensure memory is initialized
        if self.memory_manager.memory is None:
            await self.memory_manager.initialize()

        # 1. Resume Memory Check (GUIDE Section 13.1)
        if self.memory_manager.memory.resume:
            logger.info("Orchestrator: Found Resume Memory. Handling re-entry...")
            # In a real app, we'd prompt the user here. For now, we auto-resume.
            resume_entry = self.memory_manager.memory.resume
            initial_state.add_message("system", f"RESUMING TASK: {resume_entry.content}")
            # Clear resume after loading
            await self.memory_manager.clear(lanes=[MemoryLane.RESUME])

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
                state = await node_func(state) # The node MUST return the modified state
                state.current_node = current_node_name
            except Exception as e:
                state.error = f"Node execution failed: {e}"
                break
                
            if state.error:
                 break

            # 2. Determine Next Edge
            next_node = "END" 
            
            # If the node explicitly set a next_node, respect it (Phase 8 Support)
            if state.next_node and state.next_node != current_node_name:
                next_node = state.next_node
                state.next_node = None # Consume it
            elif current_node_name in self.edges:
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
            
            # PHASE 8: Metacognitive Interception
            if current_node_name != "metacognitive_observer" and next_node != "END":
                # Only intercept if moving between nodes
                state.variables["planned_next_node"] = next_node
                # Track node history for loop detection
                history = state.variables.get("node_history", [])
                history.append(current_node_name)
                state.variables["node_history"] = history
                
                # Check if we should call Metacognitor (transparently)
                if "metacognitive_observer" in self.nodes:
                    next_node = "metacognitive_observer"

            current_node_name = next_node
            state.next_node = next_node
            transitions += 1

        if hasattr(cli, 'stop_progress'):
            if state.error:
                 cli.stop_progress(success=False, msg=state.error)
            else:
                 cli.stop_progress(success=True, msg="Graph Execution Complete")
        
        # Record metrics (Phase 6)
        latency = time.time() - start_time
        await metrics_service.record_request(latency, success=(not state.error))
        
        return state
