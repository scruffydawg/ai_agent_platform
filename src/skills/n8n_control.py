# ============================================================
# SKILL: n8n Workflow Automation
# ARCHETYPE: hybrid
# ============================================================
# MCP_SERVERS:
#   - name: n8n-mcp
#     path: ~/gemini_workspace/mcp_servers/n8n-mcp/node_modules/.bin/n8n-mcp
#     source_url: https://github.com/czlonkowski/n8n-mcp
#     env_vars: N8N_API_URL, N8N_API_KEY
# CODE_TOOLS:
#   - httpx (REST calls to n8n API)
#   - python-dotenv (environment variable loading)
# DOCS:
#   - https://docs.n8n.io/api/
#   - https://github.com/czlonkowski/n8n-mcp
# ============================================================
import httpx
from typing import Any, Dict, List, Optional
from src.skills.base import BaseSkill
from src.utils.logger import logger

class N8NControlSkill(BaseSkill):
    """
    n8n Workflow Controller on steroids.
    
    Use this when:
    - You need to automate complex multi-platform flows via n8n.
    - You want to bridge native platform logic with n8n HTTP triggers.
    - You require semantic control over workflow execution and logging.
    
    Avoid when:
    - The task is a simple local Python operation (use a Native Skill instead).
    - You are interacting with a tool that has its own specialized skill/MCP.
    """
    name: str = "N8NControlSkill"
    description: str = "Advanced control for n8n workflows: list, trigger, and audit executions."
    
    # Unified Registry Metadata
    __subtype__ = "hybrid"
    __mcp_server__ = "n8n-mcp"
    __mcp_source_url__ = "https://github.com/czlonkowski/n8n-mcp"

    def __init__(self, api_url: str = "http://localhost:5678/api/v1", api_key: Optional[str] = None):
        """
        Initializes the n8n controller with the target API instance.
        
        Args:
            api_url (str): The base URL of your n8n API.
            api_key (Optional[str]): Your n8n API key for authentication.
        """
        self.api_url = api_url
        self.api_key = api_key

    async def list_workflows(self) -> Dict[str, Any]:
        """
        Retrieves a collection of all available n8n workflows.
        
        Returns:
            Dict[str, Any]: Success status and the list of workflow objects.
            
        Usage Example:
            await n8n.list_workflows()
        """
        headers = {"X-N8N-API-KEY": self.api_key} if self.api_key else {}
        async with httpx.AsyncClient(base_url=self.api_url, headers=headers) as client:
            try:
                resp = await client.get("/workflows")
                resp.raise_for_status()
                return {"status": "success", "workflows": resp.json()}
            except Exception as e:
                logger.error(f"n8n list_workflows failed: {e}")
                return {"status": "error", "message": str(e)}

    async def trigger_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """
        Synchronously triggers an execution for a specific workflow.
        
        Args:
            workflow_id (str): The unique ID of the target n8n workflow.
            
        Returns:
            Dict[str, Any]: The execution details from n8n.
            
        Usage Example:
            await n8n.trigger_workflow(workflow_id="5")
        """
        headers = {"X-N8N-API-KEY": self.api_key} if self.api_key else {}
        async with httpx.AsyncClient(base_url=self.api_url, headers=headers) as client:
            try:
                resp = await client.post(f"/workflows/{workflow_id}/executions")
                resp.raise_for_status()
                return {"status": "success", "execution": resp.json()}
            except Exception as e:
                logger.error(f"n8n trigger_workflow failed: {e}")
                return {"status": "error", "message": str(e)}
            
    async def get_execution(self, execution_id: str) -> Dict[str, Any]:
        """
        Fetches detailed audit logs for a specific n8n execution.
        
        Args:
            execution_id (str): The ID of the execution to retrieve.
            
        Returns:
            Dict[str, Any]: Full execution data including nodes and data passing.
            
        Usage Example:
            await n8n.get_execution(execution_id="1024")
        """
        headers = {"X-N8N-API-KEY": self.api_key} if self.api_key else {}
        async with httpx.AsyncClient(base_url=self.api_url, headers=headers) as client:
            try:
                resp = await client.get(f"/executions/{execution_id}")
                resp.raise_for_status()
                return {"status": "success", "execution": resp.json()}
            except Exception as e:
                logger.error(f"n8n get_execution failed: {e}")
                return {"status": "error", "message": str(e)}

n8n_control = N8NControlSkill()
