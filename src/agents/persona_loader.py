import yaml
import re
from pathlib import Path
from typing import Dict, Any, Optional
from src.utils.logger import logger

class PersonaLoader:
    def __init__(self, agents_dir: str = "src/agents/experts"):
        self.agents_dir = Path(agents_dir).resolve()
        self.agents_dir.mkdir(parents=True, exist_ok=True)
        self.base_soul_path = self.agents_dir / "SOUL.md"

    def load_persona(self, persona_name: str, live_learnings: str = "") -> Optional[Dict[str, Any]]:
        """Loads and parses an .md persona file. Optionally merges live learnings and Base Soul."""
        file_path = self.agents_dir / f"{persona_name}.md"
        if not file_path.exists():
            logger.error(f"Persona file not found: {file_path}")
            return None

        try:
            # 1. Load Base Soul
            base_soul = ""
            if self.base_soul_path.exists():
                with open(self.base_soul_path, "r", encoding="utf-8") as f:
                    base_soul = f.read()

            # 2. Load Specialist Soul
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

            # 3. Extract Sections (New "Soul" Pattern)
            soul_identity = self._extract_section(body, "SOUL")
            capabilities = self._extract_section(body, "CAPABILITIES")
            constraints = self._extract_section(body, "CONSTRAINTS")
            guidelines = self._extract_section(body, "GUIDELINES")
            memory = self._extract_section(body, "EVOLUTIONARY MEMORY")
            
            # Fallbacks for legacy files
            if not soul_identity: soul_identity = self._extract_section(body, "ROLE")
            if not guidelines: guidelines = self._extract_section(body, "GUIDELINES")
            if not memory: memory = self._extract_section(body, "EVOLUTIONARY MEMORY")

            # 4. Map and Validate AgentSpec (Hardening)
            from packages.services.validation_service import validation_service
            
            # Map legacy frontmatter to AgentSpec
            roles = frontmatter.get("roles", [])
            primary_role = frontmatter.get("role", "specialist") 
            if "orchestrator" in roles or persona_name.lower() == "guide":
                primary_role = "orchestrator"

            agent_spec = {
                "agent_id": persona_name,
                "role": primary_role,
                "mission": frontmatter.get("mission", f"Act as the {persona_name} expert within the platform."),
                "reasoning_policy": frontmatter.get("reasoning_policy", "Think step-by-step, verify observations, and act within constraints."),
                "allowed_capabilities": frontmatter.get("tools", []),
                "trust_tier_limit": frontmatter.get("trust_tier_limit", 2 if primary_role != "orchestrator" else 4),
                "memory_read_policy": frontmatter.get("memory_read_policy", ["working", "resume", "semantic", "episodic"]),
                "memory_write_policy": frontmatter.get("memory_write_policy", ["working", "session", "resume", "semantic", "episodic"]),
                "context_packet_policy": frontmatter.get("context_packet_policy", {
                    "max_context_tokens": 16000,
                    "allow_resume_priority": True,
                    "include_recent_exchange_turns": 5
                }),
                "output_envelope": frontmatter.get("output_envelope", {
                    "status": "success",
                    "summary": "Task completed."
                }),
                "handoff_policy": frontmatter.get("handoff_policy", {
                    "allowed_handoffs": ["Architect", "Security", "GUIDE"],
                    "requires_trace": True
                }),
                "failure_policy": frontmatter.get("failure_policy", {
                    "retry_allowed": True,
                    "max_retries": 1,
                    "escalate_to": "GUIDE"
                }),
                "secrets_profile": frontmatter.get("secrets_profile", "none"),
                "observability_tags": frontmatter.get("observability_tags", ["expert", persona_name.lower()])
            }

            # Enforce Hardened Role-Based Ceilings (R5)
            if agent_spec["role"] in ["specialist", "reviewer"]:
                if agent_spec["trust_tier_limit"] > 2:
                    logger.warning(f"Persona {persona_name} (role: {agent_spec['role']}) requested trust_tier_limit {agent_spec['trust_tier_limit']}. ENFORCING CEILING OF 2.")
                    agent_spec["trust_tier_limit"] = 2

            # Schema Validation
            if not validation_service.validate_agent(agent_spec):
                logger.error(f"Persona {persona_name} failed AgentSpec validation. Attempting to load with best-effort correction.")

            # 5. Generate System Prompt
            system_prompt = self._generate_system_prompt(
                base_soul=base_soul,
                soul_identity=soul_identity,
                capabilities=capabilities,
                constraints=constraints,
                memory=memory,
                live_learnings=live_learnings
            )

            return {
                "name": persona_name,
                "config": agent_spec, # Use the hardened spec
                "system_prompt": system_prompt,
                "raw_body": body
            }
        except Exception as e:
            logger.error(f"Error loading persona {persona_name}: {e}")
            return None

    def _extract_section(self, body: str, section_name: str) -> str:
        """Extracts content under a specific Markdown header."""
        pattern = rf"^#\s*{section_name}\s*\n(.*?)(?=\n#|\Z)"
        match = re.search(pattern, body, re.MULTILINE | re.DOTALL)
        return match.group(1).strip() if match else ""

    def _generate_system_prompt(self, base_soul: str, soul_identity: str, capabilities: str, constraints: str, memory: str, live_learnings: str = "") -> str:
        """Combines sections into a single system prompt using the Soul architecture."""
        prompt = []
        
        # 1. Base Shared Soul (Highest Level)
        if base_soul:
            prompt.append(f"# BASE IDENTITY & VALUES\n{base_soul}")
            
        # 2. Specialist Soul
        if soul_identity:
            prompt.append(f"# SPECIALIST SOUL\n{soul_identity}")
            
        # 3. Capabilities & Constraints
        if capabilities:
            prompt.append(f"# CAPABILITIES\n{capabilities}")
        if constraints:
            prompt.append(f"# CONSTRAINTS\n{constraints}")
        
        # 4. Adaptive Memory (Evolutionary)
        memory_combined = []
        if memory:
            memory_combined.append(memory)
        if live_learnings:
            memory_combined.append(live_learnings)
            
        if memory_combined:
            prompt.append(f"# ADAPTIVE LEARNINGS (EVOLUTIONARY MEMORY)\n" + "\n\n".join(memory_combined))
            
        return "\n\n".join(prompt)

    def list_experts(self):
        """Returns a list of all expert personas in the folder."""
        return [f.stem for f in self.agents_dir.glob("*.md")]

persona_loader = PersonaLoader()
