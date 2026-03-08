from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from src.utils.logger import logger

class BaseManifestation(ABC):
    """Base template for all Guide Manifestations."""
    
    @abstractmethod
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Core logic for the manifestation."""
        pass

class StandardSkill(BaseManifestation):
    """
    Standard native Python skill template on steroids.
    
    Use this when:
    - You need to process data using local Python libraries (e.g., pandas, Pillow).
    - You are creating complex logic that doesn't rely purely on external API calls.
    - You want high-performance, low-latency local execution.
    
    Avoid when:
    - The task is better suited for a standard MCP server (e.g., FileSystem).
    - You need to interact with a complex external platform that already has an MCP server.
    """
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        logger.info(f"Skill Manifested: {self.name}")

    async def execute(self, method_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes a specific method within the skill.
        
        Args:
            method_name (str): The name of the method to invoke.
            args (Dict[str, Any]): Key-value arguments for the method.
            
        Returns:
            Dict[str, Any]: A dictionary containing 'status' and 'result' (or 'error').
            
        Usage Example:
            await skill.execute("process_image", {"path": "input.png", "filter": "blur"})
        """
        try:
            method = getattr(self, method_name)
            if not method:
                raise AttributeError(f"Method {method_name} not found in {self.name}")
            
            result = await method(**args)
            return {"status": "success", "result": result}
        except Exception as e:
            logger.error(f"Execution Error in {self.name}.{method_name}: {str(e)}")
            return {"status": "error", "error": str(e)}

    # --- Methods to be populated by SkillForge ---
