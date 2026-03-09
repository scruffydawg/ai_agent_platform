import json
import time
import re
from pathlib import Path
from typing import List, Optional, Dict
from apps.api.settings import get_settings

class SessionService:
    def __init__(self):
        settings = get_settings()
        self.sessions_dir = Path(settings.storage_root) / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def list_sessions(self) -> List[Dict]:
        files = list(self.sessions_dir.glob("*.json"))
        sessions = []
        for f in files:
            try:
                with open(f, "r") as sf:
                    data = json.load(sf)
                    sessions.append({
                        "id": data.get("id"),
                        "title": data.get("title", data.get("id")),
                        "created_at": data.get("created_at"),
                        "last_updated": data.get("last_updated", data.get("created_at"))
                    })
            except Exception:
                pass
        
        sessions.sort(key=lambda x: x.get("last_updated", 0), reverse=True)
        return sessions

    def create_session(self, name: Optional[str] = None) -> str:
        session_id = name or f"session_{int(time.time())}"
        file_path = self.sessions_dir / f"{session_id}.json"
        
        initial_data = {
            "id": session_id,
            "created_at": time.time(),
            "messages": []
        }
        
        with open(file_path, "w") as f:
            json.dump(initial_data, f)
            
        return session_id

    def load_session(self, session_id: str) -> Optional[Dict]:
        file_path = self.sessions_dir / f"{session_id}.json"
        if not file_path.exists():
            return None
        
        with open(file_path, "r") as f:
            return json.load(f)

    def add_message(self, session_id: str, role: str, content: str) -> Optional[str]:
        file_path = self.sessions_dir / f"{session_id}.json"
        if not file_path.exists():
            return None
            
        with open(file_path, "r") as f:
            data = json.load(f)
            
        data["messages"].append({"role": role, "content": content})
        data["last_updated"] = time.time()
        
        # We'll leave titling to the route/controller for now or a separate TitleService
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)
            
        return session_id

session_service = SessionService()
