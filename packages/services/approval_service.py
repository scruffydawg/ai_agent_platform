import logging
import os
import uuid
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from apps.api.settings import get_settings

logger = logging.getLogger(__name__)
Base = declarative_base()

class ApprovalRequestModel(Base):
    __tablename__ = "approval_requests"
    id = Column(String, primary_key=True)
    tool_name = Column(String)
    arguments = Column(Text) # JSON string
    requester = Column(String)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    decided_at = Column(DateTime, nullable=True)

class ApprovalService:
    """
    Service for managing human-in-the-loop approvals with Postgres persistence.
    """
    def __init__(self):
        self._requests = {} # Fallback / Cache
        self.engine = None
        self.Session = None
        
        db_url = os.getenv("DATABASE_URL")
        if db_url:
            try:
                self.engine = create_engine(db_url)
                Base.metadata.create_all(self.engine)
                self.Session = sessionmaker(bind=self.engine)
                logger.info("ApprovalService Postgres persistence initialized")
            except Exception as e:
                logger.error(f"Failed to initialize ApprovalService DB: {e}")

    async def request_approval(self, tool_name: str, arguments: Dict[str, Any], requester: str = "orchestrator") -> str:
        req_id = str(uuid.uuid4())
        
        # In-memory fallback
        self._requests[req_id] = {
            "id": req_id,
            "tool_name": tool_name,
            "arguments": arguments,
            "requester": requester,
            "status": "pending",
            "created_at": datetime.utcnow()
        }

        if self.Session:
            try:
                with self.Session() as session:
                    db_req = ApprovalRequestModel(
                        id=req_id,
                        tool_name=tool_name,
                        arguments=json.dumps(arguments),
                        requester=requester,
                        status="pending"
                    )
                    session.add(db_req)
                    session.commit()
            except Exception as e:
                logger.error(f"Failed to persist approval request {req_id}: {e}")

        logger.info(f"Approval requested for {tool_name} (ID: {req_id})")
        return req_id

    async def get_request(self, request_id: str) -> Optional[Dict[str, Any]]:
        if self.Session:
            try:
                with self.Session() as session:
                    db_req = session.query(ApprovalRequestModel).filter_by(id=request_id).first()
                    if db_req:
                        return {
                            "id": db_req.id,
                            "tool_name": db_req.tool_name,
                            "arguments": json.loads(db_req.arguments),
                            "requester": db_req.requester,
                            "status": db_req.status,
                            "created_at": db_req.created_at
                        }
            except Exception as e:
                logger.error(f"Failed to get request from DB {request_id}: {e}")
        return self._requests.get(request_id)

    async def get_requests(self) -> List[Dict[str, Any]]:
        if self.Session:
            try:
                with self.Session() as session:
                    db_reqs = session.query(ApprovalRequestModel).all()
                    return [{
                        "id": r.id,
                        "tool_name": r.tool_name,
                        "status": r.status,
                        "created_at": r.created_at
                    } for r in db_reqs]
            except Exception as e:
                logger.error(f"Failed to get requests from DB: {e}")
        return list(self._requests.values())

    async def decide(self, request_id: str, approved: bool):
        status = "approved" if approved else "denied"
        now = datetime.utcnow()
        
        if request_id in self._requests:
            self._requests[request_id]["status"] = status
            self._requests[request_id]["decided_at"] = now

        if self.Session:
            try:
                with self.Session() as session:
                    db_req = session.query(ApprovalRequestModel).filter_by(id=request_id).first()
                    if db_req:
                        db_req.status = status
                        db_req.decided_at = now
                        session.commit()
            except Exception as e:
                logger.error(f"Failed to update approval decision for {request_id}: {e}")

        logger.info(f"Approval {request_id} {status}")

# Singleton
approval_service = ApprovalService()
