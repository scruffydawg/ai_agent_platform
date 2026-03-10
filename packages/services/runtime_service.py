import logging
import asyncio
import json
import httpx
from typing import Dict, Any, Optional, List, AsyncGenerator
from packages.services.event_service import event_service
from packages.runtime.orchestration.graph_runner import GraphRunner
from apps.api.settings import get_settings
from src.utils.tool_loader import dynamic_tools
from src.utils.tool_validator import tool_validator
from src.memory.broker import MemoryBroker
from src.memory.storage import MemoryStorage, MemoryLane, MemoryEntry

logger = logging.getLogger(__name__)

class RuntimeService:
    """
    Facade for managing graph execution and agent runtime.
    """
    def __init__(self):
        self._active_runners: Dict[str, GraphRunner] = {}
        self._execution_history: List[Dict[str, Any]] = []
        self.settings = get_settings()
        self.memory_storage = MemoryStorage()
        self.memory_broker = MemoryBroker(token_budget=16384) # Match model ctx

    async def run_graph(self, graph_data: Dict[str, Any], inputs: Dict[str, Any] = None) -> str:
        execution_id = f"exec_{int(asyncio.get_event_loop().time())}"
        
        logger.info(f"Starting graph execution {execution_id}")
        
        # In V2, we create a dedicated runner for each execution
        runner = GraphRunner(graph_data)
        self._active_runners[execution_id] = runner
        
        # Emit 'started' event
        await event_service.publish({
            "type": "runtime_event",
            "execution_id": execution_id,
            "status": "started",
            "timestamp": asyncio.get_event_loop().time()
        })
        
        # Run in background
        asyncio.create_task(self._execute(execution_id, runner, inputs or {}))
        
        return execution_id

    async def _execute(self, execution_id: str, runner: GraphRunner, inputs: Dict[str, Any]):
        try:
            result = await runner.run(inputs)
            
            # Record history
            self._execution_history.append({
                "id": execution_id,
                "status": "completed",
                "result": result
            })
            
            await event_service.publish({
                "type": "runtime_event",
                "execution_id": execution_id,
                "status": "completed",
                "result": result
            })
        except Exception as e:
            logger.error(f"Graph execution {execution_id} failed: {e}")
            await event_service.publish({
                "type": "runtime_event",
                "execution_id": execution_id,
                "status": "failed",
                "error": str(e)
            })
        finally:
            if execution_id in self._active_runners:
                del self._active_runners[execution_id]

    async def chat_stream(self, prompt: str, history: List[Dict] = None, expert: str = "guide", session_id: str = "default") -> AsyncGenerator[str, None]:
        model = self.settings.default_model
        
        # Load Agent Memory (Async)
        memory = await self.memory_storage.load_memory(expert)
        if not memory:
            # Initialize default memory if it doesn't exist
            from src.memory.storage import AgentMemory
            system_content = f"You are {expert.upper()}, a concise AI navigator. Use MARKDOWN. Use Tables for options."
            memory = AgentMemory(agent_id=expert, system_prompt=system_content)
            await self.memory_storage.save_memory(memory)

        # Sync history to Session Memory (Phase 1 Stabilization)
        if history:
            # Sync all history items that aren't already in session
            current_contents = {m.content for m in memory.session}
            for h in history:
                if h.get('content') not in current_contents:
                    memory.session.append(MemoryEntry(
                        role=h['role'], 
                        content=h['content'], 
                        lane=MemoryLane.SESSION,
                        provenance={"source": "history_sync"}
                    ))

        # 1. Brokered Context Assembly (Phase 3 v5 Architecture)
        current_messages = await self.memory_broker.assemble_context_packet(prompt, memory)
        
        # 2. Append the current user prompt (Mandatory for LLM response)
        current_messages.append({"role": "user", "content": prompt})
        
        tools_def = dynamic_tools.get_schemas()
        
        # Phase 13.6: ContextPacket Hardening (R5)
        from packages.services.validation_service import validation_service
        # (Simplified bridge for R5 validation while migrating to v5)
        v2_context_packet = {
            "packet_id": f"pkt_{int(asyncio.get_event_loop().time())}",
            "task": {"task_id": "chat_session_v5", "objective": prompt[:100], "task_depth": 0},
            "runtime_state": {"task_stage": "initial_routing", "percent_complete": 0, "next_action": "llm_generation"},
            "recent_exchange": history or [],
            "memory": {"working": {}, "resume": {"available": False}, "semantic": {}, "episodic": {}},
            "retrieved_knowledge": [],
            "policy_constraints": {"trust_tier_limit": 4 if expert == "guide" else 2, "blocked_actions": [], "policy_reference": "DEFAULT_CHAT_POLICY"},
            "trace_metadata": {"request_id": f"req_{int(asyncio.get_event_loop().time())}", "route_id": f"chat_{expert}"}
        }
        
        if not validation_service.validate_context_packet(v2_context_packet):
            logger.error("ContextPacket validation FAILED. Hardening policy breach.")
            # For now we log and proceed, but in production we might block.

        # Phase 13.9: AgentToken Issuance (R5)
        from packages.services.agent_token_service import agent_token_service
        agent_token = agent_token_service.issue_token(
            agent_id=expert,
            role="orchestrator" if expert == "guide" else "specialist",
            session_id=session_id or "default"
        )
        logger.info(f"AgentToken issued for {expert}: {agent_token[:10]}...")

        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                for _ in range(5): # Max 5 loops
                    response = await client.post(
                        f"{self.settings.llm_base_url}/api/chat",
                        json={
                            "model": model,
                            "messages": current_messages,
                            "stream": False,
                            "tools": tools_def,
                            "options": {
                                "num_ctx": 16384 # User requested 16k
                            }
                        }
                    )
                    response.raise_for_status()
                    data = response.json()
                    msg = data.get("message", {})
                    tool_calls = msg.get("tool_calls", [])

                    if tool_calls:
                        current_messages.append(msg)
                        for tc in tool_calls:
                            func_name = tc.get("function", {}).get("name")
                            args = tc.get("function", {}).get("arguments", {})
                            yield f"data: {json.dumps({'content': f'\\n\\n*🛠️ Executing `{func_name}`...*\\n'})}\n\n"
                            
                            is_valid, validated_args_or_error = tool_validator.validate_args(func_name, args)
                            if is_valid:
                                res = await dynamic_tools.execute(func_name, validated_args_or_error)
                                result_str = json.dumps(res, default=str)
                            else:
                                result_str = validated_args_or_error
                                
                            current_messages.append({"role": "tool", "name": func_name, "content": result_str})
                            yield f"data: {json.dumps({'content': f'*(Tool complete)*\\n\\n'})}\n\n"
                        continue
                    else:
                        content = msg.get("content", "")
                        chunk_size = 20
                        for i in range(0, len(content), chunk_size):
                            yield f"data: {json.dumps({'content': content[i:i+chunk_size]})}\n\n"
                            await asyncio.sleep(0.01)
                        break
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    async def stop_execution(self, execution_id: str):
        if execution_id in self._active_runners:
            logger.info(f"Stopping execution {execution_id}")
            self._active_runners[execution_id].halt()
            del self._active_runners[execution_id]

    def get_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        if execution_id in self._active_runners:
            return {"status": "running"}
        return next((h for h in self._execution_history if h["id"] == execution_id), None)

# Singleton
runtime_service = RuntimeService()
