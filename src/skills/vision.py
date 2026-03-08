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

    def take_screenshot(self, filename: Optional[str] = None, force_buffer: bool = True) -> Optional[Dict[str, Any]]:
        """
        Captures the entire primary screen.
        
        Args:
            filename (Optional[str]): Desired output filename. Auto-generated if None.
            force_buffer (bool): If True, saves to local privacy buffer first.
            
        Returns:
            Optional[Dict[str, Any]]: Metadata including path and privacy results.
            
        Usage Example:
            vision.take_screenshot(filename="error_state.png", force_buffer=True)
        """
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
                "path": target_path,
                "filename": filename,
                "is_sensitive": is_sensitive,
                "preview": self._get_base64_preview(target_path) if is_sensitive else None
            }
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
            return None

    def finalize_capture(self, filename):
        """Moves a buffered capture to permanent storage."""
        if os.path.exists(self.buffer_path):
            final_path = os.path.join(self.storage_root, filename)
            shutil.move(self.buffer_path, final_path)
            logger.info(f"Buffered capture finalized to {final_path}")
            return final_path
        return None

    def _get_base64_preview(self, path):
        """Helper to return a base64 string for UI display."""
        try:
            with open(path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except:
            return None

    def capture_webcam(self, filename: Optional[str] = None) -> Optional[str]:
        """
        Captures a single frame from the default webcam device.
        
        Args:
            filename (Optional[str]): Output filename (.jpg). Auto-generated if None.
            
        Returns:
            Optional[str]: Absolute path to the saved image file.
            
        Usage Example:
            vision.capture_webcam(filename="user_id_check.jpg")
        """
        if not filename:
            filename = f"webcam_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        
        path = os.path.join(self.storage_root, filename)
        try:
            import cv2
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                logger.error("Could not open webcam")
                return None
            
            ret, frame = cap.read()
            if ret:
                cv2.imwrite(path, frame)
                logger.info(f"Webcam capture saved to {path}")
            
            cap.release()
            return path if ret else None
        except Exception as e:
            logger.error(f"Failed to capture webcam: {e}")
            return None

vision_skill = VisionSkill()
