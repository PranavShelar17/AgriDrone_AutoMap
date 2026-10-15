import uuid
from datetime import datetime
from sqlalchemy import String, BigInteger, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class SurveyFile(Base):
    __tablename__ = "survey_files"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    survey_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("surveys.id", ondelete="CASCADE"), nullable=False, index=True)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)  # RAW_ZIP, GEOTIFF, METADATA
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    blob_uri: Mapped[str] = mapped_column(String(500), nullable=False)
    md5_checksum: Mapped[str] = mapped_column(String(32), nullable=True)
    validation_metadata = mapped_column(JSONB, nullable=True)
    ingestion_status: Mapped[str] = mapped_column(String(30), default="PENDING", nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    survey: Mapped["Survey"] = relationship("Survey", back_populates="files")
