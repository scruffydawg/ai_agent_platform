import yaml
import re
from pathlib import Path
from typing import Dict, Any, Optional
from src.utils.logger import logger

class PersonaLoader:
    def __init__(self, agents_dir: str = "src/agents/experts"):
        self.agents_dir = Path(agents_dir).resolve()
        self.agents_dir.mkdir(parents=True, exist_ok=True)

    def load_persona(self, persona_name: str) -> Optional[Dict[str, Any]]:
        """Loads and parses an .md persona file."""
        file_path = self.agents_dir / f"{persona_name}.md"
        if not file_path.exists():
            logger.error(f"Persona file not found: {file_path}")
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Separate Frontmatter and Content
            frontmatter = {}
            body = content
            if content.startswith("---"):
                parts = re.split(r"^---\s*$", content, maxsplit=2, flags=re.MULTILINE)
                if len(parts) >= 3:
                    frontmatter = yaml.safe_load(parts[1])
                    body = parts[2]

            # Parse Standard Headers
            role = self._extract_section(body, "Role")
            guidelines = self._extract_section(body, "Guidelines")
            skills = self._extract_section(body, "Skills")
            memory = self._extract_section(body, "Evolutionary Memory")

            return {
                "name": persona_name,
                "config": frontmatter,
                "role": role,
                "guidelines": guidelines,
                "skills": skills,
                "evolutionary_memory": memory,
                "system_prompt": self._generate_system_prompt(role, guidelines, memory)
            }
        except Exception as e:
            logger.error(f"Error loading persona {persona_name}: {e}")
            return None

    def _extract_section(self, body: str, section_name: str) -> str:
        """Extracts content under a specific Markdown header."""
        pattern = rf"^#\s*{section_name}\s*\n(.*?)(?=\n#|\Z)"
        match = re.search(pattern, body, re.MULTILINE | re.DOTALL)
        return match.group(1).strip() if match else ""

    def _generate_system_prompt(self, role: str, guidelines: str, memory: str) -> str:
        """Combines sections into a single system prompt."""
        prompt = []
        if role:
            prompt.append(f"## ROLE\n{role}")
        if guidelines:
            prompt.append(f"## GUIDELINES\n{guidelines}")
        if memory:
            prompt.append(f"## EVOLUTIONARY MEMORY (LEARNED PATTERNS)\n{memory}")
        return "\n\n".join(prompt)

    def list_experts(self):
        """Returns a list of all expert personas in the folder."""
        return [f.stem for f in self.agents_dir.glob("*.md")]

persona_loader = PersonaLoader()
