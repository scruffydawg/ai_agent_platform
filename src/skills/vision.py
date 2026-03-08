import os
import shutil
import base64
import tempfile
from datetime import datetime
from PIL import Image
from src.utils.logger import logger

class VisionSkill:
    def __init__(self, storage_root=None):
        self.storage_root = storage_root or "data/vision"
        fd, self.buffer_path = tempfile.mkstemp(suffix=".png", prefix="vision_buffer_")
        os.close(fd)
        os.makedirs(self.storage_root, exist_ok=True)

    def analyze_privacy(self, image_path) -> bool:
        """Mock privacy scan."""
        return False

    def take_screenshot(self, filename=None, force_buffer=True):
        """Captures the entire screen. Can save to buffer or final storage."""
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

    def capture_webcam(self, filename=None):
        """Captures a frame from the default webcam."""
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
