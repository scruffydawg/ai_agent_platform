from googleapiclient.discovery import build
from src.utils.google_auth import OAuthHandler
from src.skills.base import BaseSkill
from src.utils.logger import logger
import base64
from typing import Dict, Any, List, Optional
from email.message import EmailMessage

class GmailSkill(BaseSkill):
    """
    Gmail management skill on steroids.
    
    Use this when:
    - You need to send high-priority emails or notifications.
    - You need to search for and parse specific email threads (receipts, logs, etc.).
    - You require OAuth2 authenticated access to a user's inbox.
    
    Avoid when:
    - You are sending bulk marketing emails (use a dedicated transactional API).
    - You only need to check for file updates (use Google Drive skill instead).
    """
    def __init__(self, client_secrets_file: str = "config/client_secrets.json"):
        """
        Initializes the Gmail service with required OAuth scopes.
        
        Args:
            client_secrets_file (str): Path to the Google Cloud credentials JSON.
        """
        # Scopes required for Gmail management
        self.scopes = ['https://www.googleapis.com/auth/gmail.send', 'https://www.googleapis.com/auth/gmail.readonly']
        self.auth_handler = OAuthHandler(client_secrets_file, self.scopes, "gmail_token")
        self.service = None

    def _get_service(self):
        if not self.service:
            creds = self.auth_handler.get_credentials()
            self.service = build('gmail', 'v1', credentials=creds)
        return self.service

    async def send_message(self, to: str, subject: str, body: str) -> Dict[str, Any]:
        """Sends a plain text email via the Gmail API."""
        try:
            service = self._get_service()
            message = EmailMessage()
            message.set_content(body)
            message['To'] = to
            message['From'] = 'me'
            message['Subject'] = subject

            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            create_message = {'raw': encoded_message}
            
            send_result = service.users().messages().send(userId="me", body=create_message).execute()
            msg_id = send_result.get('id')
            logger.info(f"Message sent. ID: {msg_id}")
            return {"status": "success", "message": f"Email sent to {to}", "data": {"message_id": msg_id}}
        except Exception as e:
            logger.error(f"Failed to send Gmail: {e}")
            return {"status": "error", "message": str(e)}

    def list_messages(self, limit: int = 10) -> Dict[str, Any]:
        """List the IDs and snippets of the latest messages."""
        try:
            service = self._get_service()
            results = service.users().messages().list(userId='me', maxResults=limit).execute()
            messages = results.get('messages', [])
            
            snippets = []
            for msg in messages:
                txt = service.users().messages().get(userId='me', id=msg['id']).execute()
                snippets.append({"id": msg['id'], "snippet": txt['snippet']})
            return {"status": "success", "data": {"messages": snippets}}
        except Exception as e:
            logger.error(f"Failed to list Gmail messages: {e}")
            return {"status": "error", "message": str(e), "data": {"messages": []}}

    def run(self, action: str, **kwargs) -> Dict[str, Any]:
        if action == "send":
            import asyncio
            return asyncio.run(self.send_message(kwargs.get("to"), kwargs.get("subject"), kwargs.get("body")))
        elif action == "list":
            return self.list_messages(kwargs.get("limit", 10))
        else:
            return {"status": "error", "message": f"Unknown action: {action}"}

gmail_skill = GmailSkill()
