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
from typing import Dict, Any, Optional, List
from src.skills.base import BaseSkill

class FileSystemSkill(BaseSkill):
    """
    Skill for reading/writing files across multiple sandboxed roots.
    Supports read-only access for sensitive directories like source code.
    """
    name = "file_system_skill"
    description = "Read or write files within authorized sandbox directories."

    def __init__(self, roots: Dict[str, str]):
        """
        roots: Dictionary mapping a virtual root name to a physical path.
               Example: {'workspace': '~/guide_storage', 'src': '~/ai_platform/src'}
        """
        self.roots = {}
        for name, path in roots.items():
            resolved = Path(path).resolve()
            resolved.mkdir(parents=True, exist_ok=True)
            self.roots[name] = {
                "path": resolved,
                "readonly": name == "src" # Convention: 'src' is always read-only
            }

    def _resolve_and_validate(self, file_path: str) -> Optional[tuple]:
        """
        Resolves a virtual path (e.g., 'src/skills/base.py') to a physical path.
        Returns (physical_path, root_config) if valid, else None.
        """
        parts = Path(file_path).parts
        if not parts:
            return None
        
        root_name = parts[0]
        sub_path = Path(*parts[1:])
        
        if root_name not in self.roots:
            # Default to first root if no prefix matches (backwards compatibility)
            root_name = list(self.roots.keys())[0]
            sub_path = Path(file_path)

        root_cfg = self.roots[root_name]
        full_path = (root_cfg["path"] / sub_path).resolve()
        
        # Verify safety
        if full_path.is_relative_to(root_cfg["path"]):
            return full_path, root_cfg, root_name
        return None

    def run(self, action: str, file_path: str, content: str = "") -> Dict[str, Any]:
        """
        action: 'read', 'write', or 'list'
        file_path: path starting with root name (e.g. 'workspace/memo.txt' or 'src/skills/')
        content: string content to write (if action=='write')
        """
        result = self._resolve_and_validate(file_path)
        if not result:
            return {"status": "error", "message": f"Security Exception: Path '{file_path}' is unauthorized or invalid."}

        full_path, root_cfg, root_name = result

        try:
            if action == 'list':
                if not full_path.exists():
                    return {"status": "error", "message": f"Path {file_path} not found."}
                items = [f.name + ("/" if f.is_dir() else "") for f in full_path.iterdir()]
                return {"status": "success", "data": {"items": sorted(items), "path": file_path}}
            
            elif action == 'write':
                if root_cfg.get("readonly"):
                    return {"status": "error", "message": f"ReadOnly Exception: Cannot write to root '{root_name}'"}
                
                full_path.parent.mkdir(parents=True, exist_ok=True)
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(content)
                return {"status": "success", "message": f"Successfully wrote to {file_path}", "data": {"file_path": file_path}}
                
            elif action == 'read':
                if not full_path.exists():
                    return {"status": "error", "message": f"File {file_path} not found."}
                with open(full_path, "r", encoding="utf-8") as f:
                    data = f.read()
                return {"status": "success", "data": {"content": data, "file_path": file_path}}
                
            else:
                 return {"status": "error", "message": f"Unsupported action: {action}"}
                 
        except Exception as e:
            return {"status": "error", "message": str(e)}
