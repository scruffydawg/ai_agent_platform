from typing import Any, Dict
from abc import ABC, abstractmethod

class BaseSkill(ABC):
    """
    Abstract Base Class for all internal Agent Skills (Tools).
    Requires a run method and a name/description for LLM interpretation.
    """
    name: str = "BaseSkill"
    description: str = "Base description"

    @abstractmethod
    def run(self, **kwargs) -> Dict[str, Any]:
        """Execute the skill with the given arguments."""
        pass
