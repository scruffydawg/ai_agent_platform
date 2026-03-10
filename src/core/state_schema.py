from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class NodeMessage(BaseModel):
    """A message passed between nodes in the StateGraph."""
    role: str
    content: str
    sender_node: str

class AgentState(BaseModel):
    """
    The canonical state object passed through the Graph Orchestrator.
    Replaces simple string passing to allow for complex, multi-turn reasoning.
    """
    messages: List[NodeMessage] = Field(default_factory=list)
    current_node: str = "START"
    next_node: Optional[str] = None
    
    # GUIDE Working Memory Support
    current_task: Optional[str] = None
    step_index: int = 0
    context_packet: List[Dict[str, str]] = Field(default_factory=list)
    
    variables: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    
    def add_message(self, role: str, content: str, sender: str = "system"):
        self.messages.append(NodeMessage(role=role, content=content, sender_node=sender))
        
    def get_last_message(self) -> Optional[NodeMessage]:
        if not self.messages:
            return None
        return self.messages[-1]
