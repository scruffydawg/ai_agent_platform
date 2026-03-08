import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from src.utils.google_auth import OAuthHandler
from src.skills.base import BaseSkill
from src.utils.logger import logger

class GoogleDriveSkill(BaseSkill):
    """
    Skill for manifestation and management of files in Google Drive.
    """
    def __init__(self, client_secrets_file: str = "config/client_secrets.json"):
        # Scopes required for Drive management
        self.scopes = ['https://www.googleapis.com/auth/drive']
        self.auth_handler = OAuthHandler(client_secrets_file, self.scopes, "google_drive_token")
        self.service = None

    def _get_service(self):
        if not self.service:
            creds = self.auth_handler.get_credentials()
            self.service = build('drive', 'v3', credentials=creds)
        return self.service

    def list_files(self, page_size: int = 10):
        """List files in the current user's drive."""
        try:
            service = self._get_service()
            results = service.files().list(
                pageSize=page_size, fields="nextPageToken, files(id, name)").execute()
            items = results.get('files', [])
            return items
        except Exception as e:
            logger.error(f"Failed to list Drive files: {e}")
            return []

    def upload_file(self, file_path: str, mime_type: str = 'application/octet-stream'):
        """Upload a local file to the root of Google Drive."""
        try:
            service = self._get_service()
            file_metadata = {'name': os.path.basename(file_path)}
            media = MediaFileUpload(file_path, mimetype=mime_type)
            file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            logger.info(f"File uploaded to Drive. ID: {file.get('id')}")
            return file.get('id')
        except Exception as e:
            logger.error(f"Failed to upload to Drive: {e}")
            return None

    def execute(self, params: dict):
        action = params.get("action")
        if action == "list":
            return self.list_files(params.get("limit", 10))
        elif action == "upload":
            return self.upload_file(params.get("path"))
        else:
            return {"error": "Unknown action"}
