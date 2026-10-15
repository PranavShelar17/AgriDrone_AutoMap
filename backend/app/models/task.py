import uuid
from typing import Optional
from datetime import datetime
from sqlalchemy import String, Boolean, Integer, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class PhotogrammetryTask(Base):
    __tablename__ = "photogrammetry_tasks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    survey_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("surveys.id", ondelete="CASCADE"), nullable=False, index=True)
    source_file_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("survey_files.id", ondelete="SET NULL"), nullable=True, index=True)
    webodm_task_uuid: Mapped[Optional[str]] = mapped_column(String(64), unique=True, nullable=True, index=True)
    resolution_preset: Mapped[str] = mapped_column(String(30), default="HIGH_RES", nullable=False)
    generate_dsm: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    generate_dtm: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    radiometric_calibration: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    options = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="SUBMITTED", nullable=False, index=True)
    progress_percent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    current_stage: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("photogrammetry_projects.id", ondelete="SET NULL"), nullable=True, index=True)
    gcp_file_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("survey_files.id", ondelete="SET NULL"), nullable=True)
    gcp_applied: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    survey: Mapped["Survey"] = relationship("Survey", back_populates="photogrammetry_tasks")
    project = relationship("PhotogrammetryProject", back_populates="tasks")
    source_file: Mapped[Optional["SurveyFile"]] = relationship("SurveyFile", foreign_keys=[source_file_id])
    gcp_file: Mapped[Optional["SurveyFile"]] = relationship("SurveyFile", foreign_keys=[gcp_file_id])
    logs: Mapped[list["TaskLog"]] = relationship("TaskLog", back_populates="task", cascade="all, delete-orphan", order_by="TaskLog.id.asc()")
    map_products: Mapped[list["MapProduct"]] = relationship("MapProduct", back_populates="source_task")


class TaskLog(Base):
    __tablename__ = "task_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    task_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("photogrammetry_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    log_level: Mapped[str] = mapped_column(String(20), default="INFO", nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    logged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    task: Mapped["PhotogrammetryTask"] = relationship("PhotogrammetryTask", back_populates="logs")
