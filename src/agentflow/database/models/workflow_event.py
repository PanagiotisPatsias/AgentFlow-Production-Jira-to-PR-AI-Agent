from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from agentflow.database.base import Base

if TYPE_CHECKING:
    from agentflow.database.models.workflow_run import WorkflowRun


class WorkflowEvent(Base):
    __tablename__ = "workflow_events"

    id = Column( Uuid, primary_key=True, default=uuid.uuid4)
    run_id = Column(Uuid, ForeignKey("workflow_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    node_name = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False)
    details = Column(JSONB, nullable=False,default=dict)
    error_message = Column(Text, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    run = relationship("WorkflowRun", back_populates="events")
