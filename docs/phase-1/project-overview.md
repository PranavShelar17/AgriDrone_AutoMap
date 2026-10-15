# AgriDrone AutoMap — Project Overview

## 1. Project Purpose and Objectives

**AgriDrone AutoMap** is an enterprise-grade agricultural drone mapping, photogrammetry processing, geospatial raster analytics, and secure map visualization platform. 

The primary purpose of AgriDrone AutoMap is to bridge the gap between raw aerial drone imagery captured over agricultural lands and actionable, scientifically grounded spatial insights for farm managers, agronomists, and agricultural stakeholders. The platform provides an end-to-end, automated, and secure pipeline that enables authorized operators to:

1. **Ingest & Validate Aerial Data**: Upload drone survey photography (RGB, multispectral) and pre-stitched GIS raster files (GeoTIFFs), strictly validating coordinate reference systems (CRS), spatial metadata, and spectral band configurations.
2. **Execute Photogrammetry**: Orchestrate automated 2D orthomosaic generation by interfacing with WebODM (OpenDroneMap) asynchronously for compatible raw aerial survey photos.
3. **Run Precision GIS Vegetation Index Algorithms**: Derive calibrated vegetation indices (including NDVI, NDRE, GNDVI, and SAVI) using high-performance Python geospatial engines (GDAL, Rasterio, NumPy) while strictly enforcing spectral prerequisites.
4. **Deliver Secure Geospatial Visualizations**: Present multi-layer raster maps, dynamic color-ramped legends, and temporal survey comparisons via an interactive web viewer built with MapLibre GL JS.
5. **Generate Data-Backed Diagnostic Reports**: Calculate transparent, pixel-level statistical distributions (mean, median, standard deviation, area coverage per health class) and synthesize them into downloadable, auditable PDF reports using ReportLab.

---

## 2. Intended Users & Stakeholders

The platform serves two primary distinct user groups with strict role boundaries:

### A. Drone Operators & Agricultural System Administrators
- **Profile**: Drone pilots, GIS technicians, and farm agronomy system admins.
- **Responsibilities**:
  - Setting up farm boundaries, field extents, and survey metadata.
  - Uploading batches of raw geotagged drone photographs or vendor-provided pre-stitched GeoTIFFs.
  - Configuring and monitoring WebODM photogrammetry reconstruction tasks.
  - Executing and verifying GIS vegetation index generation.
  - Reviewing diagnostic statistics, raster quality, and publishing verified products to farmer accounts.

### B. Farmers & Landowners (Agricultural Stakeholders)
- **Profile**: Farm owners, crop managers, agronomists, and field scouts.
- **Responsibilities**:
  - Accessing only their authorized farms, fields, and survey flights.
  - Visualizing published orthomosaics and vegetation index layers over time.
  - Inspecting zoned distribution metrics and field summary statistics.
  - Downloading published PDF survey summary reports and GIS deliverables.
  - *Strict Restriction*: Farmers cannot initiate photogrammetry jobs, reconfigure raw ingestion parameters, access backend administrative interfaces, or access surveys belonging to other farm entities.

---

## 3. Main Business and Technical Benefits

- **Decoupled Workflows**: Clear architectural separation between raw drone photogrammetry (WebODM) and direct GIS processing of existing orthomosaics (Rasterio/GDAL), preventing unnecessary processing delays and cloud compute costs.
- **Scientific Rigor**: Elimination of false vegetation indices; algorithms refuse execution unless calibrated spectral bands (e.g., genuine Near-Infrared) are verified in file metadata.
- **Auditable Provenance**: Complete data lineage tracking from camera sensor EXIF/XMP tags and WebODM processing logs down to single-band index raster generation and PDF distribution.
- **Multi-Tenant Security**: Rigorous server-side tenancy enforcement ensuring zero cross-tenant data leakage, with cloud files secured via time-limited, narrowly-scoped shared access signatures (SAS) from Microsoft Azure Blob Storage.
- **Cost-Effective Cloud Scalability**: Long-running photogrammetry and raster math jobs are offloaded to asynchronous Celery workers backed by Redis, keeping the FastAPI backend responsive.

---

## 4. Five-Page Core Architecture Scope

The web application strictly adheres to a **Five-Page Functional Architecture**. Every capability of the platform lives inside one of these five dedicated functional pages:

| Page # | Page Name | Primary Objective |
| :--- | :--- | :--- |
| **Page 1** | **Admin Dashboard & Drone Image Ingestion** | Survey creation, file upload, CRS/metadata validation, and dataset eligibility ledger. |
| **Page 2** | **WebODM Photogrammetry Processing** | Raw photograph reconstruction, photogrammetry option presets, live task monitoring, and orthomosaic registration. |
| **Page 3** | **Algorithm & Multi-Map Generation** | Spectral band validation, calibrated index generation (NDVI, NDRE, GNDVI, SAVI), and map layer management. |
| **Page 4** | **Secure Farmer Portal** | Read-only tenant view for authorized farmers to inspect surveys, toggle interactive map layers, and download verified reports. |
| **Page 5** | **Diagnostics & Actionable Insights** | Field-level statistical analysis, zoning breakdowns, system limitations reporting, and automated PDF report compilation. |

*Note: Technical endpoints (e.g., API routes, health probes) and a dedicated minimal authentication gate exist in support of these pages, but no additional functional dashboards or major modules are permitted.*

---

## 5. Expected Deliverables

### Phase 1 Deliverables (Current Phase)
- Comprehensive technical documentation suite in `docs/phase-1/` covering requirements, security, workflows, GIS validation, roadmap, and open architectural decisions.
- Updated root `README.md` reflecting project identity, tech stack, and Phase 1 completion status.
- Zero application code, zero cloud infrastructure provisioning, and zero mock data creation until formal Phase 1 sign-off.

### Future Phase Deliverables (Phases 2 – 10)
- **Phase 2**: UI/UX design blueprints and component inventory aligned with the supplied reference template.
- **Phase 3**: Architecture verification, Docker Compose baseline, and WebODM/Azure integration proofs-of-concept.
- **Phase 4**: PostgreSQL database schemas, PostGIS spatial models, and Alembic migration scripts.
- **Phase 5**: Next.js Admin Dashboard, chunked file upload pipeline, and FastAPI file validation endpoints.
- **Phase 6**: Celery worker integration with WebODM API, task polling, and orthomosaic artifact storage.
- **Phase 7**: Geospatial computation pipeline (Rasterio/NumPy) for calibrated vegetation indices.
- **Phase 8**: MapLibre GL JS multi-layer viewer, raster tile serving, and legend controls.
- **Phase 9**: Production authentication enforcement and Secure Farmer Portal role-based views.
- **Phase 10**: End-to-end integration tests, ReportLab PDF generation, documentation handover, and deployment runbooks.

---

## 6. Important Assumptions and Constraints

1. **Storage Platform**: Microsoft Azure Blob Storage is the mandatory cloud storage platform. S3 and MinIO are excluded. All raw uploads, orthomosaics, vegetation index GeoTIFFs, and generated PDFs reside in private Azure containers.
2. **Hardware & Compute**: Photogrammetry (WebODM) is CPU- and RAM-intensive (minimum recommended 16GB–32GB RAM, multi-core CPU). Direct raster calculation is memory-bound based on GeoTIFF pixel dimensions and chunk size.
3. **Reference Template Dependency**: The user has established that an external reference UI/UX template and screenshots represent the design authority. As verified during Phase 1 inspection, the workspace is currently empty; therefore, template assets must be supplied prior to commencing Phase 2.
4. **Authentication Undecided**: The specific identity provider/mechanism (e.g., JWT with FastAPI, Azure Entra ID, NextAuth/Auth.js) remains an open decision to be confirmed before Phase 4/Phase 9.
5. **No Speculative Agronomy**: The platform delivers validated mathematical raster indices and descriptive statistical zoning; it does not promise automated disease diagnosis, yield prediction, or chemical fertilizer prescriptions.
