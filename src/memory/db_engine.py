import os
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import Column, String, Float, JSON, DateTime, Integer, ForeignKey, Text, Boolean
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.dialects.postgresql import UUID, JSONB
from apps.api.settings import get_settings

Base = declarative_base()

class MemoryEntryModel(Base):
    __tablename__ = "memory_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(String, index=True)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    lane = Column(String, index=True) # session, working, resume, semantic, episodic
    source = Column(String)
    confidence = Column(Float, default=1.0)
    schema_version = Column(String, default="5.0")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # v5 Governance Fields
    provenance = Column(JSONB, default={})
    superseded_by = Column(String, nullable=True) # UUID of newer item
    meta_data = Column(JSONB, default={})

class AgentMemoryModel(Base):
    __tablename__ = "agent_memories"

    agent_id = Column(String, primary_key=True)
    system_prompt = Column(Text)
    task_status = Column(String, default="idle") # idle, active, interrupted
    schema_version = Column(String, default="5.0")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class MemoryConflictModel(Base):
    __tablename__ = "memory_conflicts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject = Column(String, index=True)
    original_id = Column(UUID(as_uuid=True))
    competitor_id = Column(UUID(as_uuid=True))
    resolution = Column(String) # superseded, merged, rejected
    detected_at = Column(DateTime, default=datetime.utcnow)

# Database Setup
settings = get_settings()
engine = create_async_engine(settings.postgres_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db_session():
    async with AsyncSessionLocal() as session:
        yield session
