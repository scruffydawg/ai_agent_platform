import os
import sys
import ast
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.skills.skill_indexer import skill_indexer
from src.utils.logger import logger

def parse_skill_file(file_path: Path):
    """
    Statically parses a skill file to extract metadata for indexing.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())

        skill_meta = {
            "name": file_path.stem,
            "filename": file_path.name,
            "description": "",
            "methods": [],
            "subtype": "skill"
        }

        for node in ast.walk(tree):
            # Extract class docstring for description
            if isinstance(node, ast.ClassDef):
                if ast.get_docstring(node):
                    skill_meta["description"] = ast.get_docstring(node).split("\n")[0]
            
            # Extract methods
            if isinstance(node, ast.FunctionDef):
                if node.name.startswith("_"): continue
                
                method_info = {
                    "name": node.name,
                    "doc": ast.get_docstring(node).split("\n")[0] if ast.get_docstring(node) else f"Execute {node.name}",
                    "params": [arg.arg for arg in node.args.args if arg.arg != "self"]
                }
                skill_meta["methods"].append(method_info)

        return skill_meta
    except Exception as e:
        logger.error(f"BootstrapIndexer: Failed to parse {file_path.name}: {e}")
        return None

def run_indexing():
    logger.info("Starting Bootstrap Skill Indexing...")
    skills_dir = PROJECT_ROOT / "src" / "skills"
    
    if not skills_dir.exists():
        logger.error(f"Skills directory not found at {skills_dir}")
        return

    indexed_count = 0
    for file in skills_dir.glob("*.py"):
        if file.name.startswith("__") or file.name in ("base.py", "skill_indexer.py") or file.name.startswith("test_"):
            continue
            
        skill_meta = parse_skill_file(file)
        if skill_meta:
            if skill_indexer.index(skill_meta):
                indexed_count += 1
    
    logger.info(f"Bootstrap Indexing Complete. Indexed {indexed_count} skills.")

if __name__ == "__main__":
    run_indexing()
