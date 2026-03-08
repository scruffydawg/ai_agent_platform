import os
import json
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

class OAuthHandler:
    """
    Standardized OAuth 2.0 Hanlder for Guide Manifestations.
    Focuses on secure token storage within the Guide Storage Schema.
    """
    def __init__(self, client_secrets_file: str, scopes: list, token_name: str):
        self.client_secrets_file = client_secrets_file
        self.scopes = scopes
        # Tokens are stored in a dedicated secure area of our storage schema
        _storage_root = os.environ.get("GUIDE_STORAGE_ROOT", str(Path.home() / "guide_storage"))
        self.token_path = os.path.join(_storage_root, "data", "secure", f"{token_name}.json")
        os.makedirs(os.path.dirname(self.token_path), exist_ok=True)

    def get_credentials(self) -> Credentials:
        creds = None
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, self.scopes)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.client_secrets_file, self.scopes)
                creds = flow.run_local_server(port=0)
            
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())
        
        return creds
