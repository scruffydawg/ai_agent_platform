import os
from pathlib import Path
from src.utils.logger import logger

from typing import Optional

class StorageMapper:
    def __init__(self):
        self.root_path: Optional[Path] = None

    def set_root(self, path: str):
        self.root_path = Path(path).resolve()
        if not self.root_path.exists():
            logger.error(f"Storage path does not exist: {self.root_path}")
            return False
        return True

    def initialize_schema(self):
        if not self.root_path:
            return False
        
        directories = [
            "skills",
            "mcp",
            "docs",
            "data",
            "logs",
            "models"
        ]
        
        try:
            for d in directories:
                (self.root_path / d).mkdir(parents=True, exist_ok=True)
            logger.info(f"Standard AI Schema initialized at: {self.root_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize schema: {e}")
            return False

storage_mapper = StorageMapper()
