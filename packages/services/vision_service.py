from typing import Optional, Dict, Any
from src.skills.vision import vision_skill

class VisionService:
    def take_screenshot(self, filename: Optional[str] = None) -> Dict[str, Any]:
        return vision_skill.take_screenshot(filename=filename)

    def capture_webcam(self, confirm: bool = False) -> Dict[str, Any]:
        if not confirm:
            return {"status": "privacy_confirmation_required"}
        return vision_skill.capture_webcam()

vision_service = VisionService()
