import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, Integer, Numeric, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geometry
from app.db.base import Base


class Algorithm(Base):
    __tablename__ = "algorithms"

    code: Mapped[str] = mapped_column(String(30), primary_key=True)  # NDVI, NDRE, VARI, GLI, SAVI, GNDVI
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    required_sensor: Mapped[str] = mapped_column(String(50), nullable=False)  # MULTISPECTRAL, RGB
    formula_spec = mapped_column(JSONB, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    jobs: Mapped[list["AlgorithmJob"]] = relationship("AlgorithmJob", back_populates="algorithm")


class AlgorithmJob(Base):
    __tablename__ = "algorithm_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    batch_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    input_product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("map_products.id", ondelete="RESTRICT"), nullable=False, index=True)
    algorithm_code: Mapped[str] = mapped_column(String(30), ForeignKey("algorithms.code"), nullable=False, index=True)
    parameters = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="QUEUED", nullable=False, index=True)
    current_stage: Mapped[str] = mapped_column(String(100), default="QUEUED", nullable=True)
    progress_percent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    output_product_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("map_products.id", ondelete="SET NULL"), nullable=True, index=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    algorithm: Mapped["Algorithm"] = relationship("Algorithm", back_populates="jobs")
    input_product: Mapped["MapProduct"] = relationship("MapProduct", foreign_keys=[input_product_id])
    output_product: Mapped[Optional["MapProduct"]] = relationship("MapProduct", foreign_keys=[output_product_id])


class MapProduct(Base):
    __tablename__ = "map_products"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    survey_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("surveys.id", ondelete="CASCADE"), nullable=False, index=True)
    source_task_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("photogrammetry_tasks.id", ondelete="SET NULL"), nullable=True)
    source_job_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("algorithm_jobs.id", ondelete="SET NULL"), nullable=True)
    product_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # ORTHOPHOTO, DSM, INDEX_NDVI, etc
    blob_uri: Mapped[str] = mapped_column(String(500), nullable=False)
    is_cog: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    band_count: Mapped[int] = mapped_column(Integer, nullable=False)
    crs_epsg: Mapped[str] = mapped_column(String(20), nullable=False)
    resolution_cm_px: Mapped[Optional[float]] = mapped_column(Numeric(8, 2), nullable=True)
    extent_geom = mapped_column(Geometry(geometry_type="POLYGON", srid=4326), nullable=True)
    statistical_summary = mapped_column(JSONB, nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    survey: Mapped["Survey"] = relationship("Survey", back_populates="map_products")
    source_task: Mapped[Optional["PhotogrammetryTask"]] = relationship("PhotogrammetryTask", back_populates="map_products")
    zonal_statistics: Mapped[list["ZonalStatistic"]] = relationship("ZonalStatistic", back_populates="map_product", cascade="all, delete-orphan")


class ZonalStatistic(Base):
    __tablename__ = "zonal_statistics"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    map_product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("map_products.id", ondelete="CASCADE"), nullable=False, index=True)
    zone_name: Mapped[str] = mapped_column(String(100), nullable=False)
    min_val: Mapped[float] = mapped_column(Numeric(6, 3), nullable=False)
    max_val: Mapped[float] = mapped_column(Numeric(6, 3), nullable=False)
    area_hectares: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    area_percentage: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    map_product: Mapped["MapProduct"] = relationship("MapProduct", back_populates="zonal_statistics")
