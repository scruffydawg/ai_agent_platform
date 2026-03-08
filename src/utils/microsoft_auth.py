import os
import json
import msal
from pathlib import Path
from src.utils.logger import logger

class MicrosoftAuthHandler:
    """
    OAuth 2.0 Handler for Microsoft Graph API manifestations.
    Uses MSAL for secure token management within the Guide Storage Schema.
    """
    def __init__(self, client_id: str, client_secret: str, tenant_id: str, scopes: list):
        self.client_id = client_id
        self.client_secret = client_secret
        self.authority = f"https://login.microsoftonline.com/{tenant_id}"
        self.scopes = scopes
        _storage_root = os.environ.get("GUIDE_STORAGE_ROOT", str(Path.home() / "guide_storage"))
        self.cache_path = os.path.join(_storage_root, "data", "secure", "ms_graph_token.json")
        
        self.app = msal.ConfidentialClientApplication(
            self.client_id,
            authority=self.authority,
            client_credential=self.client_secret,
        )

    def get_access_token(self):
        """Acquire a token from cache or via client credentials."""
        # For a background agent, we typically use Client Credentials (App-only)
        # unless user-delegated access is explicitly required.
        result = self.app.acquire_token_silent(self.scopes, account=None)
        
        if not result:
            logger.info("Acquiring new token for MS Graph...")
            result = self.app.acquire_token_for_client(scopes=self.scopes)
            
        if "access_token" in result:
            return result["access_token"]
        else:
            logger.error(f"Failed to acquire MS Graph token: {result.get('error_description')}")
            return None
