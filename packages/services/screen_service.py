from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class UIScreen(BaseModel):
    id: str
    title: str
    layout: str # 'bento', 'panel', 'split'
    components: List[Dict[str, Any]]

class ScreenService:
    """
    Generates dynamic UI manifests for agents to "manifest" their state visually.
    """
    def __init__(self):
        self.active_screens: Dict[str, UIScreen] = {}

    def generate_screen(self, agent_id: str, data: Dict[str, Any]) -> UIScreen:
        """
        Creates a UI schema based on the data type.
        """
        screen_id = f"screen_{agent_id}_{len(self.active_screens)}"
        
        # Simple heuristic for bento layout if multiple keys
        layout = "bento" if len(data.keys()) > 2 else "panel"
        
        components = []
        for key, value in data.items():
            comp_type = "text"
            if isinstance(value, list): comp_type = "list"
            elif isinstance(value, dict): comp_type = "chart" if "values" in value else "json"
            
            components.append({
                "id": f"{screen_id}_{key}",
                "type": comp_type,
                "label": key.replace("_", " ").title(),
                "content": value
            })
            
        screen = UIScreen(
            id=screen_id,
            title=f"Insights from {agent_id}",
            layout=layout,
            components=components
        )
        
        self.active_screens[screen_id] = screen
        return screen

screen_service = ScreenService()
