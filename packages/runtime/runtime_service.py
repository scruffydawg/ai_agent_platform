import asyncio
import uuid
import time
import json
import httpx
from typing import Dict, Any, List, Optional, AsyncGenerator
from src.core.orchestrator import StateGraphOrchestrator
from packages.runtime.orchestration.event_bus import event_bus
from src.core.state import state_manager
from apps.api.settings import get_settings
from src.utils.tool_loader import dynamic_tools
from src.utils.tool_validator import tool_validator

class RuntimeService:
    def __init__(self):
        self.orchestrator = StateGraphOrchestrator()
        self.settings = get_settings()

    async def start_run(self, session_id: str, prompt: str) -> str:
        run_id = f"run_{int(time.time() * 1000)}"
        asyncio.create_task(self._execute_run(run_id, session_id, prompt))
        return run_id

    async def _execute_run(self, run_id: str, session_id: str, prompt: str):
        await event_bus.publish({"type": "run_started", "run_id": run_id, "session_id": session_id})
        try:
            state_manager.add_active_task({"id": run_id, "name": f"Run: {prompt[:30]}", "status": "running"})
            # In V1 this was a loop over nodes, we'll keep that for now
            nodes = ["Observer", "Researcher", "Analyst", "Writer"]
            for node in nodes:
                if state_manager.is_halted(): break
                await event_bus.publish({"type": "state_update", "run_id": run_id, "node": node, "status": "active"})
                await asyncio.sleep(1) # Simulation
            
            state_manager.complete_task(run_id)
            await event_bus.publish({"type": "run_complete", "run_id": run_id})
        except Exception as e:
            state_manager.fail_task(run_id, str(e))
            await event_bus.publish({"type": "run_error", "run_id": run_id, "error": str(e)})

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

runtime_service = RuntimeService()
