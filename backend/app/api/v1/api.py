from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    health,
    farms,
    fields,
    surveys,
    ingestion,
    dashboard,
    photogrammetry,
    algorithms,
    maps,
    reports,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication & Farmer Access"])
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(farms.router, prefix="/farms", tags=["Farms"])
api_router.include_router(fields.router, prefix="/fields", tags=["Fields"])
api_router.include_router(surveys.router, prefix="/surveys", tags=["Surveys"])
api_router.include_router(ingestion.router, prefix="/ingestion", tags=["Drone Ingestion"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Admin Dashboard"])
api_router.include_router(photogrammetry.router, prefix="/photogrammetry", tags=["WebODM Photogrammetry"])
api_router.include_router(algorithms.router, prefix="/algorithms", tags=["Vegetation Indices & Algorithms"])
api_router.include_router(maps.router, prefix="/maps", tags=["Interactive GIS Maps"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])

# Alias /cluster/status for Phase 3 API contract alignment
api_router.add_api_route(
    "/cluster/status",
    photogrammetry.get_cluster_status,
    methods=["GET"],
    tags=["Cluster Infrastructure"],
    response_model=photogrammetry.ClusterStatusResponse,
    summary="WebODM / NodeODM worker cluster status",
)
