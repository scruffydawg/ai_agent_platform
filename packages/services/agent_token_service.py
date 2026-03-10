import jwt
import datetime
import os
from typing import Dict, Any, Optional

class AgentTokenService:
    """
    Issued signed JWTs to agents for the duration of a task or session.
    Part of R5 Hardening to ensure identity non-repudiation.
    """
    def __init__(self, secret_key: str = "r5_hardened_fallback_secret"):
        self.secret_key = os.getenv("JWT_SECRET", secret_key)
        self.algorithm = "HS256"

    def issue_token(self, agent_id: str, role: str, session_id: str, expires_in_seconds: int = 3600) -> str:
        """
        Generates a JWT for an agent.
        """
        payload = {
            "sub": agent_id,
            "role": role,
            "session_id": session_id,
            "iat": datetime.datetime.utcnow(),
            "exp": datetime.datetime.utcnow() + datetime.timedelta(seconds=expires_in_seconds)
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verifies an agent token and returns the payload.
        """
        try:
            return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

# Singleton
agent_token_service = AgentTokenService()
