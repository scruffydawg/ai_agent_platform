import json
import logging
from typing import Any, Dict, Optional, Tuple
from pydantic import BaseModel, ValidationError, Field, field_validator

logger = logging.getLogger(__name__)

class CanvasPushSchema(BaseModel):
    mode: str = Field(description="The UI tab mode. Must be one of: 'MD', 'CODE', 'PREVIEW', 'DOC'.")
    content: str = Field(description="The actual text content to render on the canvas.")
    filename: Optional[str] = Field(default=None, description="Optional filename for context or saving.")

    @field_validator('mode')
    @classmethod
    def normalize_mode(cls, v: str) -> str:
        mapping = {
            "markdown": "MD", "md": "MD",
            "code": "CODE", "python": "CODE", "javascript": "CODE",
            "preview": "PREVIEW", "html": "PREVIEW",
            "document": "DOC", "doc": "DOC", "markdown_doc": "DOC"
        }
        val = v.lower().strip()
        return mapping.get(val, v.upper())

class WebSearchSchema(BaseModel):
    query: str = Field(description="The search query string.")

class FileSystemReadSchema(BaseModel):
    action: str = Field(pattern="^(read)$")
    file_path: str

class FileSystemWriteSchema(BaseModel):
    action: str = Field(pattern="^(write)$")
    file_path: str
    content: str

class DockerListSchema(BaseModel):
    # No required args for list_containers
    pass

class ToolValidator:
    """
    Validates tool payloads against strict Pydantic schemas.
    If validation fails, returns (False, ErrorMessage) to feed back to the LLM.
    If it succeeds, returns (True, ValidatedDict).
    """
    
    # Map of tool names to their corresponding Pydantic schemas
    SCHEMAS = {
        "push_to_canvas": CanvasPushSchema,
        "search_web": WebSearchSchema,
        "read_file": FileSystemReadSchema,
        "write_file": FileSystemWriteSchema,
        "list_containers": DockerListSchema
    }

    @classmethod
    def validate_args(cls, tool_name: str, args: Dict[str, Any]) -> Tuple[bool, Any]:
        """
        Validates the arguments for a given tool.
        Returns (is_valid, result_or_error_string).
        """
        if tool_name not in cls.SCHEMAS:
            # If we don't have a strict schema for it yet, pass it through
            return True, args
            
        schema_cls = cls.SCHEMAS[tool_name]
        try:
            # Attempt to parse and validate
            validated = schema_cls(**args)
            return True, validated.model_dump()
        except ValidationError as e:
            # Format a clear error message for the LLM to fix it
            error_msg = f"Tool argument validation failed for '{tool_name}'. Please correct the following errors and retry:\n"
            for err in e.errors():
                loc = ".".join(str(l) for l in err['loc'])
                error_msg += f"- Field '{loc}': {err['msg']}\n"
            
            logger.warning(f"Validation failed for {tool_name}: {error_msg}")
            return False, error_msg

tool_validator = ToolValidator()
