import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from src.utils.google_auth import OAuthHandler
from src.skills.base import BaseSkill
from src.utils.logger import logger
from typing import Dict, Any, List

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

    def list_files(self, limit: int = 10) -> Dict[str, Any]:
        """List files in the current user's drive."""
        try:
            service = self._get_service()
            results = service.files().list(
                pageSize=limit, fields="nextPageToken, files(id, name)").execute()
            items = results.get('files', [])
            return {"status": "success", "data": {"files": items}}
        except Exception as e:
            logger.error(f"Failed to list Drive files: {e}")
            return {"status": "error", "message": str(e), "data": {"files": []}}

    def upload_file(self, file_path: str, mime_type: str = 'application/octet-stream') -> Dict[str, Any]:
        """Upload a local file to the root of Google Drive."""
        try:
            service = self._get_service()
            file_metadata = {'name': os.path.basename(file_path)}
            media = MediaFileUpload(file_path, mimetype=mime_type)
            file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            file_id = file.get('id')
            logger.info(f"File uploaded to Drive. ID: {file_id}")
            return {"status": "success", "message": f"Uploaded {file_path} to Drive", "data": {"file_id": file_id}}
        except Exception as e:
            logger.error(f"Failed to upload to Drive: {e}")
            return {"status": "error", "message": str(e)}

    def run(self, action: str, **kwargs) -> Dict[str, Any]:
        if action == "list":
            return self.list_files(kwargs.get("limit", 10))
        elif action == "upload":
            return self.upload_file(kwargs.get("path"))
        else:
            return {"status": "error", "message": f"Unknown action: {action}"}

gdrive_skill = GoogleDriveSkill()
