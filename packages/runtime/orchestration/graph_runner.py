import asyncio
import logging
import json
import uuid
from typing import Dict, Any, List, Optional, Callable
from packages.services.event_service import event_service
from packages.services.approval_service import approval_service

logger = logging.getLogger(__name__)

from src.utils.tool_loader import dynamic_tools

class GraphRunner:
    """
    Modular graph execution engine for V2.
    Decouples node logic from graph traversal and state management.
    """
    def __init__(self, graph_data: Dict[str, Any]):
        self.graph_id = graph_data.get("id", str(uuid.uuid4()))
        self.nodes = graph_data.get("nodes", []) # List of node definitions
        self.edges = graph_data.get("edges", []) # List of edge definitions
        self.state: Dict[str, Any] = {"history": [], "variables": {}}
        self._halted = False

    async def run(self, inputs: Dict[str, Any] = None) -> Dict[str, Any]:
        """Executes the graph based on the provided topology."""
        if inputs:
            self.state["variables"].update(inputs)

        start_node_id = self._get_start_node()
        if not start_node_id:
            logger.warning(f"No start node found for graph {self.graph_id}")
            return self.state
            
        current_node_id = start_node_id
        logger.info(f"Starting graph {self.graph_id} at node {current_node_id}")

        while current_node_id and not self._halted:
            # 1. Emit Node Started Event
            await self._emit_event("node_started", {"node_id": current_node_id})

            # 2. Execute Node logic
            try:
                node_output = await self._execute_node(current_node_id)
                self.state["history"].append({
                    "node_id": current_node_id,
                    "output": node_output,
                    "timestamp": asyncio.get_event_loop().time()
                })
            except Exception as e:
                logger.error(f"Node {current_node_id} failed: {e}")
                await self._emit_event("node_failed", {"node_id": current_node_id, "error": str(e)})
                break

            # 3. Emit Node Completed Event
            await self._emit_event("node_completed", {"node_id": current_node_id, "output": node_output})

            # 4. Determine Next Node
            current_node_id = self._get_next_node(current_node_id, node_output)

        logger.info(f"Graph {self.graph_id} finished execution")
        return self.state

    async def _execute_node(self, node_id: str) -> Dict[str, Any]:
        """
        Executes a single node by calling a tool or agent.
        """
        node_def = next((n for n in self.nodes if n["id"] == node_id), None)
        if not node_def:
            raise ValueError(f"Node {node_id} not found in graph definition")

        tool_name = node_def.get("tool", node_id)
        
        # Check if this node requires approval
        if node_def.get("requires_approval"):
            logger.info(f"Node {node_id} requires approval")
            req_id = await approval_service.request_approval(
                tool_name=tool_name,
                arguments=self.state["variables"],
                requester=self.graph_id
            )
            
            # Wait for approval
            while True:
                req = await approval_service.get_request(req_id)
                if req and req["status"] != "pending":
                    if req["status"] == "approved":
                        break
                    else:
                        raise Exception(f"Node {node_id} denied by user")
                await asyncio.sleep(1)

        # Actual tool execution
        if tool_name in dynamic_tools.tool_functions:
            logger.info(f"Executing tool: {tool_name}")
            result = await dynamic_tools.execute(tool_name, self.state["variables"])
            return {"result": result, "status": "success"}
        
        # Fallback simulation
        await asyncio.sleep(0.5) 
        return {"result": f"Simulated {node_id}", "status": "success"}

    def _get_start_node(self) -> Optional[str]:
        # Simple heuristic: first node in list or one with no incoming edges
        if not self.nodes: return None
        return self.nodes[0]["id"]

    def _get_next_node(self, current_id: str, output: Dict[str, Any]) -> Optional[str]:
        # Look for matching edge
        for edge in self.edges:
            if edge["source"] == current_id:
                # Basic direct edge
                return edge["target"]
        return None # End of graph

    async def _emit_event(self, event_type: str, data: Dict[str, Any]):
        await event_service.publish({
            "type": "graph_event",
            "graph_id": self.graph_id,
            "event": event_type,
            "data": data,
            "timestamp": asyncio.get_event_loop().time()
        })

    def halt(self):
        self._halted = True
