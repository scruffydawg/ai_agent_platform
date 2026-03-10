import os
import logging
from pathlib import Path
from src.config import DEFAULT_STORAGE_ROOT
from src.skills.base import BaseSkill

logger = logging.getLogger(__name__)

class DeleteSavedFileSkill(BaseSkill):
    """
    Rollback capability specifically for deleting files that were saved as attachments.
    Crucial for R5 hardening to reverse external mutations.
    """
    def __init__(self, storage_root: str = DEFAULT_STORAGE_ROOT):
        super().__init__()
        self.storage_root = Path(storage_root).resolve()

    def run(self, filename: str) -> dict:
        """
        Deletes a specific file from the attachment storage.
        
        Args:
            filename (str): The name of the file to delete (must be within storage_root).
        """
        file_path = self.storage_root / filename
        
        # Security: Prevent path traversal
        if not str(file_path).startswith(str(self.storage_root)):
             return {"status": "error", "message": "Security Violation: Access denied outside storage root."}

        try:
            if file_path.exists():
                os.remove(file_path)
                logger.info(f"Rollback: Deleted file {filename}")
                return {"status": "success", "message": f"File {filename} deleted successfully (Rollback)."}
            else:
                return {"status": "success", "message": f"File {filename} already absent. No action needed."}
        except Exception as e:
            logger.error(f"Failed to delete file {filename} during rollback: {e}")
            return {"status": "error", "message": f"Rollback failed: {str(e)}"}

# Expert instance
delete_saved_file = DeleteSavedFileSkill()
