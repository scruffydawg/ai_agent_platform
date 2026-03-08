import httpx
from typing import Any, Dict, List, Optional
from src.skills.base import BaseSkill
from src.utils.logger import logger

class N8NControlSkill(BaseSkill):
    """
    Skill for controlling n8n workflows natively via API.
    Replaces the n8n-mcp container with a native manifestation.
    """
    name: str = "N8NControlSkill"
    description: str = "Control n8n workflows. Can list workflows, trigger executions, and retrieve logs."

    def __init__(self, api_url: str = "http://localhost:5678/api/v1", api_key: Optional[str] = None):
        self.api_url = api_url
        self.api_key = api_key

    async def run(self, action: str, **kwargs) -> Dict[str, Any]:
        """Async run for API calls."""
        headers = {}
        if self.api_key:
            headers["X-N8N-API-KEY"] = self.api_key

        async with httpx.AsyncClient(base_url=self.api_url, headers=headers, timeout=10.0) as client:
            try:
                if action == "list_workflows":
                    resp = await client.get("/workflows")
                    resp.raise_for_status()
                    return {"status": "success", "workflows": resp.json()}

                elif action == "trigger_workflow":
                    workflow_id = kwargs.get("id")
                    if not workflow_id:
                        return {"status": "error", "message": "Workflow ID required."}
                    resp = await client.post(f"/workflows/{workflow_id}/executions")
                    resp.raise_for_status()
                    return {"status": "success", "execution": resp.json()}

                elif action == "get_execution":
                    execution_id = kwargs.get("id")
                    if not execution_id:
                        return {"status": "error", "message": "Execution ID required."}
                    resp = await client.get(f"/executions/{execution_id}")
                    resp.raise_for_status()
                    return {"status": "success", "execution": resp.json()}

                else:
                    return {"status": "error", "message": f"Unknown action: {action}"}

            except httpx.HTTPError as e:
                logger.error(f"n8n API '{action}' failed: {e}")
                return {"status": "error", "message": str(e)}

n8n_control = N8NControlSkill()
