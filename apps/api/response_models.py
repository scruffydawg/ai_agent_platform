from typing import Any, Optional, Dict, List
from pydantic import BaseModel, Field

class SuccessResponse(BaseModel):
    status: str = "success"
    data: Optional[Any] = None
    message: Optional[str] = None

class ErrorResponse(BaseModel):
    status: str = "error"
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None

class PaginatedResponse(SuccessResponse):
    total: int
    page: int
    size: int
