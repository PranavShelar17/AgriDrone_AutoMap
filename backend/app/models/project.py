import uuid
from typing import Optional, List
from datetime import datetime
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class PhotogrammetryProject(Base):
    __tablename__ = "photogrammetry_projects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Domain associations within AgriDrone
    farm_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("farms.id", ondelete="SET NULL"), nullable=True, index=True)
    field_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("fields.id", ondelete="SET NULL"), nullable=True, index=True)
    survey_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("surveys.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # WebODM upstream container mapping
    webodm_project_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    
    # Ownership & Status
    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(30), default="ACTIVE", nullable=False, index=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    farm = relationship("Farm", foreign_keys=[farm_id])
    field = relationship("Field", foreign_keys=[field_id])
    survey = relationship("Survey", foreign_keys=[survey_id])
    created_by = relationship("User", foreign_keys=[created_by_id])
    tasks: Mapped[List["PhotogrammetryTask"]] = relationship("PhotogrammetryTask", back_populates="project", cascade="all, delete-orphan", order_by="PhotogrammetryTask.started_at.desc()")
