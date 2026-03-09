from fastapi import Depends, Header, HTTPException, status, Request
from apps.api.settings import AppSettings, get_settings

def settings_dep() -> AppSettings:
    return get_settings()

def require_auth(
    request: Request,
    settings: AppSettings = Depends(settings_dep),
) -> None:
    if not settings.auth_enabled or not settings.operator_api_key:
        return
    
    auth = request.headers.get("Authorization")
    if not auth or auth != f"Bearer {settings.operator_api_key}":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )
