# AgriDrone AutoMap — Technical Risk Register & Mitigation Strategy
## Document Reference: `docs/phase-3/technical-risk-register.md`
**Phase**: Phase 3 — System Architecture, Technical Validation & Implementation Blueprint  
**Status**: APPROVED ARCHITECTURE BLUEPRINT  
**Version**: 1.0.0  

---

## 1. Risk Assessment Matrix Overview

The following register tracks critical architectural, operational, and scientific risks identified across the AgriDrone AutoMap platform. Each risk is categorized by Likelihood and Impact, assigned a concrete mitigation, and tied to an architectural verification method.

| Risk ID | Category | Description | Likelihood | Impact | Mitigation Strategy | Verification Method | Responsible Component | User Approval Required? |
| :--- | :--- | :--- | :---: | :---: | :--- | :--- | :--- | :---: |
| **RSK-01** | Photogrammetry | NodeODM worker runs out of RAM (OOM) during large survey (> 800 photos). | High | High | Enforce pre-flight survey image limits; configure WebODM chunking/split-merge; enforce minimum 32GB RAM worker sizing. | Load testing with 1,000-photo simulated survey dataset. | Celery Worker / WebODM | No |
| **RSK-02** | Scientific | User calculates NDVI/NDRE on ordinary 3-band RGB imagery producing invalid data. | High | Critical | **Hard scientific input gating**: UI and backend strictly lock NIR indices when RGB input is detected; enable visible indices (VARI, GLI) instead. | Unit tests in `test_index_calculator.py` asserting 400 Bad Request on RGB-NDVI. | FastAPI / Algorithm Router | No |
| **RSK-03** | Geospatial | Multi-gigabyte GeoTIFF freezes browser when loaded directly into MapLibre GL JS. | High | High | Require Cloud-Optimized GeoTIFF (COG) conversion before map registration; serve streamable XYZ tiles via TiTiler / FastAPI tile proxy. | Network inspection verifying windowed HTTP range-request tile fetches in Chrome. | GDAL Worker / MapLibre | No |
| **RSK-04** | Cloud Storage | Uploading 5GB drone survey times out or exhausts FastAPI server memory. | Medium | High | Direct client-to-Azure chunked BlockBlob uploads via 15-minute SAS tokens; zero binary payload traverses the FastAPI process. | Integration test verifying 2GB file upload directly to Azure with progress tracking. | Ingestion UI / Azure Blob SDK | No |
| **RSK-05** | Security | Farmer accesses competitor farm survey data by manipulating survey ID in URL (IDOR). | Medium | Critical | Server-side multi-tenant ownership enforcement (`WHERE farm.owner_id = current_user.id`) on every endpoint; SAS tokens minted only for verified owners. | Security integration test attempting cross-tenant survey retrieval (asserting 403 Forbidden). | Auth & Security Middleware | No |
| **RSK-06** | Infrastructure | WebODM photogrammetry takes 3+ hours and drops HTTP connection. | High | Medium | Completely decouple job dispatch from synchronous HTTP; Celery polling task persists progress in PostgreSQL; client polls REST API. | End-to-end task dispatch test confirming client receives 202 Accepted and tracking URL. | Celery / Redis / PostgreSQL | No |
| **RSK-07** | Data Quality | Uploaded imagery lacks valid Coordinate Reference System (CRS) or EXIF georeferencing. | Medium | Medium | Automated pre-flight raster inspection flags unreferenced files with Status `'REJECTED'`; displays clear recovery instructions to user. | Test case in `test_raster_service.py` with non-georeferenced TIFF. | Ingestion Worker (GDAL) | No |
| **RSK-08** | Compliance | Agronomic PDF reports are misinterpreted as certified disease diagnoses or yield warranties. | Medium | High | Mandatory bold legal disclaimer on Page 5 and PDF report cover explicitly categorizing indices as optical reflectance indicators. | Review of ReportLab PDF template generation script. | Report Compiler | No |
| **RSK-09** | Architecture | Unresolved authentication provider delays frontend login integration. | Medium | Low | Decoupled `AuthManager` interface with JWT mock support allows full platform development to proceed without hard vendor lock-in. | Unit testing of abstract auth interface with mock tokens. | Security Core | **Yes** (Auth choice pending) |
| **RSK-10** | Cost | Idle high-compute WebODM GPU nodes incur excessive cloud hosting expenses. | Medium | Medium | Auto-shutdown idle NodeODM VM scale sets when Celery photogrammetry queue depth is 0 for > 30 minutes. | Cloud cost alerts and VM scale-in verification. | DevOps / IaC | **Yes** (Hosting approval) |
