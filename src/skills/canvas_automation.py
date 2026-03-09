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
        
    async def push_to_canvas(self, mode: str, content: str, filename: str = None) -> str:
        """
        Pushes content to the interactive Canvas UI and saves it locally.
        
        Args:
            mode: The type of canvas tab to open ('MD', 'CODE', 'PREVIEW', 'DOC')
            content: The string content to render (markdown text, code, HTML)
            filename: Optional filename to save the content as locally.
            
        Returns:
            A status string indicating success or failure.
        """
        # Normalize mode string from LLM to match frontend strict cases
        mode = mode.upper() if mode else "MD"
        if mode in ["MARKDOWN", "TEXT"]: mode = "MD"
        if mode in ["DOCUMENT", "PDF"]: mode = "DOC"
        
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
                
        # Import the unified schema definition
        from src.utils.tool_validator import CanvasPushSchema
        
        # Coerce the dictionary into the standard schema
        schema_model = CanvasPushSchema(mode=mode, content=content, filename=filename)
        
        # Broadcast to frontend directly without HTTP request to avoid deadlocking the server's event loop!
        try:
            payload = {
                "type": "canvas_push",
                "mode": schema_model.mode,
                "content": schema_model.content,
                "metadata": {
                    "filename": schema_model.filename or "artifact",
                    "saved_path": saved_path
                }
            }
            import sys
            import asyncio
            if "src.server" in sys.modules:
                ws_manager = sys.modules["src.server"].ws_manager
                asyncio.create_task(ws_manager.broadcast(payload))
            else:
                # Fallback to HTTP if server module isn't strictly imported yet
                async def _send():
                    try:
                        async with httpx.AsyncClient() as client:
                            await client.post(f"{self.api_base}/canvas/event", json=payload, timeout=3.0)
                    except:
                        pass
                asyncio.create_task(_send())
                
            result_msg = f"Successfully pushed to Canvas tab '{mode}'."
            if saved_path:
                result_msg += f" Content saved locally to {saved_path}."
            return result_msg
        except Exception as e:
            logger.error(f"Canvas push broadcast failed: {e}")
            return f"Failed to push to canvas: {str(e)}"

# Instantiate the global skill helper
canvas_automation_skill = CanvasAutomationSkill(DEFAULT_STORAGE_ROOT)
