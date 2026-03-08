from typing import Dict, Any
from .manifestation_mcp import MCPIntegration
from .manifestation_skill import StandardSkill

class HybridManifestation:
    """
    Unified template for complex manifestations.
    Combines native processing (Skill) with protocol-based interaction (MCP).
    """
    def __init__(self, name: str, mcp_url: str):
        self.local_logic = StandardSkill(name, f"Hybrid component for {name}")
        self.external_nexus = MCPIntegration(mcp_url)

    async def execute_swarm_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        # 1. Logic via Skill
        pre_processed = self.local_logic.execute(task_data)
        
        # 2. Action via MCP
        result = await self.external_nexus.call_tool("process", pre_processed)
        
        return result
