import os
import shutil
import logging
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional
from src.config import DEFAULT_STORAGE_ROOT
from src.skills.base import BaseSkill

logger = logging.getLogger(__name__)

class SaveAttachmentSkill(BaseSkill):
    """
    Saves an attachment (simulated or real message part) to storage.
    Includes R5 hardening metadata for rollbacks.
    """
    name = "save_attachment"
    description = "Save an email attachment to a specified folder. Durable external mutation."
    
    # R5 Hardening Metadata
    side_effect_class = "external_mutation"
    rollback_policy = {
        "rollback_supported": True,
        "rollback_capability": "delete_saved_file",
        "rollback_window_seconds": 300
    }

    def __init__(self, storage_root: str = DEFAULT_STORAGE_ROOT):
        super().__init__()
        self.storage_root = Path(storage_root).resolve()

    def run(self, message_id: str, attachment_index: int, target_folder: str, filename_override: Optional[str] = None) -> Dict[str, Any]:
        """
        Simulates saving an attachment.
        """
        folder_path = self.storage_root / target_folder
        folder_path.mkdir(parents=True, exist_ok=True)
        
        filename = filename_override or f"attach_{message_id}_{attachment_index}.dat"
        file_path = folder_path / filename
        
        # Security: Prevent path traversal
        if not str(file_path).startswith(str(self.storage_root)):
             return {"status": "error", "message": "Security Violation: Access denied outside storage root."}

        try:
            # Simulate writing byte content
            content = f"Simulated attachment content for message {message_id}, index {attachment_index}".encode('utf-8')
            with open(file_path, "wb") as f:
                f.write(content)
            
            checksum = hashlib.sha256(content).hexdigest()
            size = len(content)
            
            logger.info(f"Saved attachment to {file_path}")
            
            return {
                "status": "success",
                "data": {
                    "saved_path": str(file_path),
                    "file_size_bytes": size,
                    "checksum_sha256": checksum
                }
            }
        except Exception as e:
            logger.error(f"Failed to save attachment: {e}")
            return {"status": "error", "message": str(e)}

# Expert instance
save_attachment = SaveAttachmentSkill()
