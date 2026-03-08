import httpx
from src.utils.microsoft_auth import MicrosoftAuthHandler
from src.skills.base import BaseSkill
from src.utils.logger import logger

class Office365Skill(BaseSkill):
    """
    Skill for manifestation and management of Microsoft 365 services (Graph API).
    """
    def __init__(self, client_id: str, client_secret: str, tenant_id: str):
        self.scopes = ['https://graph.microsoft.com/.default']
        self.auth_handler = MicrosoftAuthHandler(client_id, client_secret, tenant_id, self.scopes)

    async def list_files(self, limit: int = 10):
        """List files in OneDrive for Business."""
        token = self.auth_handler.get_access_token()
        if not token:
            return []

        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {token}"}
            # List items in root drive
            url = f"https://graph.microsoft.com/v1.0/me/drive/root/children?$top={limit}"
            resp = await client.get(url, headers=headers)
            
            if resp.status_code == 200:
                data = resp.json()
                return data.get("value", [])
            else:
                logger.error(f"MS Graph Error: {resp.text}")
                return []

    async def send_mail(self, to: str, subject: str, content: str):
        """Send an email via Outlook (Graph API)."""
        token = self.auth_handler.get_access_token()
        if not token:
            return False

        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            url = "https://graph.microsoft.com/v1.0/me/sendMail"
            payload = {
                "message": {
                    "subject": subject,
                    "body": {
                        "contentType": "Text",
                        "content": content
                    },
                    "toRecipients": [
                        {
                            "emailAddress": {
                                "address": to
                            }
                        }
                    ]
                }
            }
            resp = await client.post(url, headers=headers, json=payload)
            return resp.status_code == 202

    async def execute(self, params: dict):
        action = params.get("action")
        if action == "list_files":
            return await self.list_files(params.get("limit", 10))
        elif action == "send_mail":
            return await self.send_mail(params.get("to"), params.get("subject"), params.get("content"))
        else:
            return {"error": "Unknown action"}
