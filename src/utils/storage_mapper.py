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
            "mcp_servers",
            "code_tools",
            "registries",
            "docs",
            "data",
            "logs",
            "models"
        ]
        
        try:
            for d in directories:
                (self.root_path / d).mkdir(parents=True, exist_ok=True)
            
            # Write a schema legend for the user
            legend_path = self.root_path / "schema_legend.md"
            if not legend_path.exists():
                legend_path.write_text(
                    "# Three-Pillar Storage Schema\n\n"
                    "- **skills/**: Python files implementing actual capability logic (`src/skills/` may be aliased here).\n"
                    "- **mcp_servers/**: Installed third-party MCP server environments (e.g. n8n-mcp, sqlite-mcp).\n"
                    "- **code_tools/**: Reusable Python libraries, scripts, and execution node tools.\n"
                    "- **registries/**: Lightweight JSON index files (`skills_registry.json`, `mcp_registry.json`, `code_tools_registry.json`) for LLM progressive disclosure.\n"
                )

            logger.info(f"Standard AI Schema initialized at: {self.root_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize schema: {e}")
            return False

storage_mapper = StorageMapper()
