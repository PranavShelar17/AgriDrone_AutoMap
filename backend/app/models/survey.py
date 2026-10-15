import uuid
from datetime import datetime, date
from sqlalchemy import String, Date, Numeric, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geometry
from app.db.base import Base


class Survey(Base):
    __tablename__ = "surveys"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    field_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("fields.id", ondelete="CASCADE"), nullable=False, index=True)
    survey_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    flight_date: Mapped[date] = mapped_column(Date, nullable=False)
    drone_model: Mapped[str] = mapped_column(String(100), nullable=True)
    sensor_type: Mapped[str] = mapped_column(String(50), default="RGB", nullable=False)
    flight_altitude_m: Mapped[float] = mapped_column(Numeric(6, 2), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="DRAFT", nullable=False, index=True)
    coverage_geom = mapped_column(Geometry(geometry_type="POLYGON", srid=4326), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    field: Mapped["Field"] = relationship("Field", back_populates="surveys")
    files: Mapped[list["SurveyFile"]] = relationship("SurveyFile", back_populates="survey", cascade="all, delete-orphan")
    photogrammetry_tasks: Mapped[list["PhotogrammetryTask"]] = relationship("PhotogrammetryTask", back_populates="survey", cascade="all, delete-orphan")
    map_products: Mapped[list["MapProduct"]] = relationship("MapProduct", back_populates="survey", cascade="all, delete-orphan")
    reports: Mapped[list["Report"]] = relationship("Report", back_populates="survey", cascade="all, delete-orphan")
