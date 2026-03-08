import os
from pathlib import Path
import httpx
from src.utils.logger import logger
from src.config import DEFAULT_STORAGE_ROOT

class CanvasAutomationSkill:
    """
    A skill that allows the agent to autonomously push content (markdown, code, etc.)
    directly to the frontend Research Canvas. It also saves the artifacts locally.
    """
    
    def __init__(self, workspace_root: Path):
        self.workspace_root = Path(workspace_root)
        self.canvas_dir = self.workspace_root / "canvas_artifacts"
        self.canvas_dir.mkdir(parents=True, exist_ok=True)
        # Assuming the FastAPI server runs on localhost:8001
        self.api_base = "http://localhost:8001"
        
    def push_to_canvas(self, mode: str, content: str, filename: str = None) -> str:
        """
        Pushes content to the interactive Canvas UI and saves it locally.
        
        Args:
            mode: The type of canvas tab to open ('MD', 'CODE', 'PREVIEW', 'DOC')
            content: The string content to render (markdown text, code, HTML)
            filename: Optional filename to save the content as locally.
            
        Returns:
            A status string indicating success or failure.
        """
        # Save locally if a filename is provided
        saved_path = None
        if filename:
            try:
                safe_name = filename.replace("/", "_").replace("..", "")
                file_path = self.canvas_dir / safe_name
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                saved_path = str(file_path)
            except Exception as e:
                logger.error(f"Failed to save canvas artifact: {e}")
                
        # Broadcast to frontend via server endpoint
        try:
            payload = {
                "type": "canvas_push",
                "mode": mode,
                "content": content,
                "metadata": {
                    "filename": filename or "artifact",
                    "saved_path": saved_path
                }
            }
            # We hit our own server's internal endpoint synchronously to trigger the websocket
            response = httpx.post(f"{self.api_base}/canvas/event", json=payload, timeout=5.0)
            if response.status_code == 200:
                result_msg = f"Successfully pushed to Canvas tab '{mode}'."
                if saved_path:
                    result_msg += f" Content saved locally to {saved_path}."
                return result_msg
            else:
                return f"Failed to push to canvas. Server responded with {response.status_code}."
        except Exception as e:
            logger.error(f"Canvas push broadcast failed: {e}")
            return f"Failed to push to canvas: {str(e)}"

# Instantiate the global skill helper
canvas_automation_skill = CanvasAutomationSkill(DEFAULT_STORAGE_ROOT)
