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

logger = logging.getLogger(__name__)

class RuntimeService:
    """
    Facade for managing graph execution and agent runtime.
    """
    def __init__(self):
        self._active_runners: Dict[str, GraphRunner] = {}
        self._execution_history: List[Dict[str, Any]] = []
        self.settings = get_settings()

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

    async def chat_stream(self, prompt: str, history: List[Dict] = None, expert: str = "guide") -> AsyncGenerator[str, None]:
        model = self.settings.default_model
        system_content = f"You are {expert.upper()}, a concise AI navigator. Use MARKDOWN. Use Tables for options."
        messages = [{"role": "system", "content": system_content}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": prompt})

        tools_def = dynamic_tools.get_schemas()
        current_messages = messages.copy()
        
        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                for _ in range(5): # Max 5 loops
                    response = await client.post(
                        f"{self.settings.llm_base_url}/api/chat",
                        json={
                            "model": model,
                            "messages": current_messages,
                            "stream": False,
                            "tools": tools_def
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
                            yield f"data: {json.dumps({'content': f'\\n\\n*🛠️ Executing `{func_name}`...*\\n'})}\\n\\n"
                            
                            is_valid, validated_args_or_error = tool_validator.validate_args(func_name, args)
                            if is_valid:
                                res = await dynamic_tools.execute(func_name, validated_args_or_error)
                                result_str = json.dumps(res, default=str)
                            else:
                                result_str = validated_args_or_error
                                
                            current_messages.append({"role": "tool", "name": func_name, "content": result_str})
                            yield f"data: {json.dumps({'content': f'*(Tool complete)*\\n\\n'})}\\n\\n"
                        continue
                    else:
                        content = msg.get("content", "")
                        chunk_size = 20
                        for i in range(0, len(content), chunk_size):
                            yield f"data: {json.dumps({'content': content[i:i+chunk_size]})}\\n\\n"
                            await asyncio.sleep(0.01)
                        break
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\\n\\n"

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
