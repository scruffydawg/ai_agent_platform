# Legacy Redirect for V2 Architecture
from apps.api.app import app

# This file is retained for backward compatibility with scripts 
# that expect src.server:app. Standard V2 entry is 'uvicorn apps.api.app:app'
