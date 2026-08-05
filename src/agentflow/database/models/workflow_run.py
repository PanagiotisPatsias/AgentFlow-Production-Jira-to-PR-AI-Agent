from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, String, Text, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from agentflow.database.base import Base

if TYPE_CHECKING:
    from agentflow.database.models.workflow_event import WorkflowEvent


class WorkflowRun(Base):
    __tablename__ = "workflow_runs"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    ticket_key = Column(String(100), nullable=False, index=True)
    repository_url = Column(Text, nullable=False)
    status = Column(String(50), nullable=False,index=True)
    current_stage = Column(String(100), nullable=True)
    celery_task_id = Column(String(255), nullable=True, unique=True)
    input_data = Column(JSONB, nullable=False, default=dict)
    result_data = Column(JSONB,nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True),nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    events = relationship("WorkflowEvent", back_populates="run", cascade="all, delete-orphan")
