import os
import shutil
import base64
import tempfile
from typing import Dict, Any, List, Optional
from datetime import datetime
from PIL import Image
from src.utils.logger import logger

class VisionSkill:
    """
    Vision and Screen Capture skill on steroids.
    
    Use this when:
    - You need to capture screenshots for visual debugging or analysis.
    - You need to access the webcam for real-world visual input.
    - You require privacy-aware buffered capture management.
    
    Avoid when:
    - You only need to verify element existence in a browser (use browser skills for that).
    - High-frequency video stream processing is required (this is for discrete frame capture).
    """
    def __init__(self, storage_root: Optional[str] = None):
        """
        Initializes the vision storage and temporary buffers.
        
        Args:
            storage_root (Optional[str]): Permanent storage path. Defaults to 'data/vision'.
        """
        self.storage_root = storage_root or "data/vision"
        fd, self.buffer_path = tempfile.mkstemp(suffix=".png", prefix="vision_buffer_")
        os.close(fd)
        os.makedirs(self.storage_root, exist_ok=True)

    def analyze_privacy(self, image_path) -> bool:
        """Mock privacy scan."""
        return False

    def take_screenshot(self, filename: Optional[str] = None, force_buffer: bool = True) -> Dict[str, Any]:
        """Captures the entire primary screen."""
        if not filename:
            filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        target_path = self.buffer_path if force_buffer else os.path.join(self.storage_root, filename)
        
        try:
            import pyautogui
            screenshot = pyautogui.screenshot()
            screenshot.save(target_path)
            logger.info(f"Screenshot captured to {target_path}")
            
            is_sensitive = False
            if force_buffer:
                is_sensitive = self.analyze_privacy(target_path)
            
            return {
                "status": "success",
                "message": f"Screenshot captured to {target_path}",
                "data": {
                    "path": target_path,
                    "filename": filename,
                    "is_sensitive": is_sensitive,
                    "preview": self._get_base64_preview(target_path) if is_sensitive else None
                }
            }
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
            return {"status": "error", "message": str(e)}

    def capture_webcam(self, filename: Optional[str] = None) -> Dict[str, Any]:
        """Captures a single frame from the default webcam device."""
        if not filename:
            filename = f"webcam_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        
        path = os.path.join(self.storage_root, filename)
        try:
            import cv2
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                return {"status": "error", "message": "Could not open webcam"}
            
            ret, frame = cap.read()
            if ret:
                cv2.imwrite(path, frame)
                logger.info(f"Webcam capture saved to {path}")
            
            cap.release()
            if ret:
                return {"status": "success", "message": f"Webcam capture saved to {path}", "data": {"path": path}}
            return {"status": "error", "message": "Failed to read from webcam"}
        except Exception as e:
            logger.error(f"Failed to capture webcam: {e}")
            return {"status": "error", "message": str(e)}

vision_skill = VisionSkill()
