from sqlalchemy import Column, String, DateTime, JSON, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from src.utils.db import Base

class SecurityEvent(Base):
    __tablename__ = "security_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_time = Column(DateTime, default=datetime.utcnow)
    channel = Column(String, nullable=True)
    session_id = Column(String, nullable=True)
    event_type = Column(String)  # 'injection_attempt', 'unknown_sender', 'output_redaction', 'validation_failure'
    severity = Column(String)    # 'low', 'medium', 'high'
    details = Column(JSON, nullable=True)
    resolved = Column(Boolean, default=False)
