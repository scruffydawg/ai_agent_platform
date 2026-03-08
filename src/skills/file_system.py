# ============================================================
# SKILL: File System Operations
# ARCHETYPE: native
# ============================================================
# MCP_SERVERS:
#   - None (Native Python OS calls)
# CODE_TOOLS:
#   - os, pathlib (Standard libraries)
# DOCS:
#   - https://docs.python.org/3/library/os.html
# ============================================================
import os
from pathlib import Path
from typing import Dict, Any
from src.skills.base import BaseSkill

class FileSystemSkill(BaseSkill):
    """
    Skill for reading/writing files, strictly sandboxed to a specific directory.
    Prevents path traversal vulnerabilities.
    """
    name = "file_system_skill"
    description = "Read or write files within the designated sandbox directory."

    def __init__(self, sandbox_dir: Path):
        self.sandbox_dir = sandbox_dir.resolve()
        self.sandbox_dir.mkdir(parents=True, exist_ok=True)

    def _is_safe_path(self, target_path: str) -> bool:
        """
        Validates that the requested path resolves to a location inside the sandbox.
        """
        # Resolve path to absolute, removing any ../ or ./
        try:
             # We use Path(target) instead of resolving to ensure it doesn't need to exist yet 
             # to be checked for safety, but we check if its base is our sandbox
             requested_path = (self.sandbox_dir / target_path).resolve()
        except RuntimeError:
             return False

        # Verify the resolved path starts with the sandbox directory
        return requested_path.is_relative_to(self.sandbox_dir)

    def run(self, action: str, file_path: str, content: str = "") -> Dict[str, Any]:
        """
        action: 'read' or 'write'
        file_path: relative path within the sandbox
        content: string content to write (if action=='write')
        """
        if not self._is_safe_path(file_path):
            return {"status": "error", "message": f"Security Exception: Path '{file_path}' attempts to traverse outside the sandbox."}

        full_path = (self.sandbox_dir / file_path).resolve()

        try:
            if action == 'write':
                # Ensure parent directories exist
                full_path.parent.mkdir(parents=True, exist_ok=True)
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(content)
                return {"status": "success", "message": f"Successfully wrote to {file_path}"}
                
            elif action == 'read':
                if not full_path.exists():
                    return {"status": "error", "message": f"File {file_path} not found."}
                with open(full_path, "r", encoding="utf-8") as f:
                    data = f.read()
                return {"status": "success", "content": data}
                
            else:
                 return {"status": "error", "message": f"Unsupported action: {action}"}
                 
        except Exception as e:
            return {"status": "error", "message": str(e)}
