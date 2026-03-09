from fastapi import APIRouter, HTTPException, Depends
from typing import List
from packages.services.approval_service import approval_service
from apps.api.response_models import SuccessResponse, ErrorResponse

router = APIRouter()

@router.get("", response_model=SuccessResponse)
async def list_approvals():
    """
    List all pending and past approval requests.
    """
    requests = await approval_service.get_requests()
    return SuccessResponse(data=requests)

@router.get("/{request_id}", response_model=SuccessResponse)
async def get_approval(request_id: str):
    req = await approval_service.get_request(request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Approval request not found")
    return SuccessResponse(data=req)

@router.post("/{request_id}/decide", response_model=SuccessResponse)
async def decide_approval(request_id: str, approved: bool):
    req = await approval_service.get_request(request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Approval request not found")
    
    await approval_service.decide(request_id, approved)
    return SuccessResponse(message=f"Request {request_id} {'approved' if approved else 'denied'}")
