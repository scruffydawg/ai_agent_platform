import os
import json
from typing import Dict, Any, List, Optional
from src.utils.logger import logger

class GovernanceService:
    """
    Centralized Governance for AI Tool Execution.
    Enforces policies on sensitivity, blocklists, and resource quotas.
    """
    def __init__(self):
        self.blocklist = ["rm -rf", "mkfs", "dd if=/dev/zero"]
        self.sensitive_tools = [
            "delete_saved_file", 
            "docker_management", 
            "file_system_operations.delete",
            "mcp_execute_command"
        ]
        # Default policy: tools in sensitive_tools require 'requires_approval' flag
        self.requires_approval = True

    def validate_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates if a tool call is safe to proceed.
        Returns: { "allowed": bool, "reason": str, "requires_approval": bool }
        """
        # 1. Blocklist Check
        arg_str = json.dumps(arguments).lower()
        for forbidden in self.blocklist:
            if forbidden in arg_str:
                logger.warning(f"Governance: Blocked tool call '{tool_name}' due to forbidden pattern: {forbidden}")
                return {
                    "allowed": False, 
                    "reason": f"Security Violation: Arguments contain forbidden pattern '{forbidden}'",
                    "requires_approval": False
                }

        # 2. Sensitivity Check
        is_sensitive = tool_name in self.sensitive_tools
        
        return {
            "allowed": True,
            "reason": "OK",
            "requires_approval": is_sensitive
        }

governance_service = GovernanceService()
