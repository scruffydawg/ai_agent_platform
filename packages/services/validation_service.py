import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from jsonschema import validate, ValidationError

logger = logging.getLogger(__name__)

class ValidationService:
    def __init__(self, schemas_dir: str = "apps/api/schemas"):
        self.schemas_dir = Path(schemas_dir).resolve()
        self._schemas = {}
        self._load_schemas()

    def _load_schemas(self):
        if not self.schemas_dir.exists():
            logger.warning(f"Schemas directory not found: {self.schemas_dir}")
            return

        for schema_file in self.schemas_dir.glob("*.schema.json"):
            try:
                with open(schema_file, "r") as f:
                    self._schemas[schema_file.stem] = json.load(f)
                logger.info(f"Loaded schema: {schema_file.name}")
            except Exception as e:
                logger.error(f"Failed to load schema {schema_file.name}: {e}")

    def validate_agent(self, agent_data: Dict[str, Any]) -> bool:
        return self._validate("agent", {"AgentSpec": agent_data})

    def validate_capability(self, capability_data: Dict[str, Any]) -> bool:
        return self._validate("capability", {"CapabilitySpec": capability_data})

    def validate_context_packet(self, packet_data: Dict[str, Any]) -> bool:
        return self._validate("contextpacket", {"ContextPacket": packet_data})

    def _validate(self, schema_name: str, data: Any) -> bool:
        schema = self._schemas.get(f"{schema_name}.schema" if ".schema" not in schema_name else schema_name)
        if not schema:
            # Fallback to key-based lookup if prompt names differ
            schema = self._schemas.get(schema_name)
            
        if not schema:
            logger.error(f"Schema not found: {schema_name}")
            return False

        try:
            validate(instance=data, schema=schema)
            return True
        except ValidationError as e:
            logger.error(f"Validation error in {schema_name}: {e.message}")
            return False
        except Exception as e:
            logger.error(f"Unexpected validation error in {schema_name}: {e}")
            return False

validation_service = ValidationService()
