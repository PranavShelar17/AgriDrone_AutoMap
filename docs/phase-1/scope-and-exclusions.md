# AgriDrone AutoMap — Scope & Exclusions

## 1. Executive Summary & Scope Boundary

The scope of **AgriDrone AutoMap** is strictly bounded to the ingestion, photogrammetric reconstruction, geospatial index generation, interactive visualization, and PDF reporting of agricultural drone datasets across **exactly five main functional pages**.

Any capability, screen, service, or integration not explicitly detailed in the functional specification is considered **Out of Scope** and requires formal change control review before adoption.

---

## 2. In-Scope Features & Modules

The platform includes the following verified technical capabilities across its lifecycle:

### A. Data Ingestion & Administrative Management (Page 1)
- Farm, Field (boundary geometry), and Survey (flight event) creation and association.
- Secure upload of drone image sets (JPG, DNG, TIFF raw aerial photos with EXIF/XMP GPS metadata).
- Direct upload of pre-stitched, georeferenced raster products (GeoTIFF / COG).
- Server-side pre-flight metadata extraction and validation (CRS, spatial resolution, band count, file integrity).
- Storage of uploaded assets directly in private Microsoft Azure Blob Storage containers.
- Ingestion audit ledger displaying dataset eligibility (e.g., eligible for photogrammetry vs. eligible for direct GIS processing).

### B. WebODM Photogrammetry Processing (Page 2)
- Asynchronous dispatch of raw photo collections to WebODM / OpenDroneMap instances via REST API.
- Task configuration management (e.g., orthophoto resolution, feature quality, DSM generation flags).
- Live job monitoring (Queued, Processing, Completed, Failed) via background Celery tasks and Redis.
- Streaming WebODM task log viewer for diagnostics.
- Automatic registration and ingestion of generated orthomosaics and digital surface models into the platform catalog.

### C. Spectral Algorithm & Multi-Map Generation (Page 3)
- Spectral band verification ensuring genuine sensor requirements are met before calculation.
- Automated mathematical raster calculation using Rasterio, GDAL, and NumPy for:
  - **NDVI** (Normalized Difference Vegetation Index): Requires validated Near-Infrared (NIR) and Red.
  - **NDRE** (Normalized Difference Red Edge): Requires validated NIR and Red Edge.
  - **GNDVI** (Green Normalized Difference Vegetation Index): Requires validated NIR and Green.
  - **SAVI** (Soil Adjusted Vegetation Index): Requires validated NIR, Red, and documented soil factor $L$.
- Dynamic color-ramp classification and Cloud Optimized GeoTIFF (COG) generation.
- Calculation metadata persistence (provenance, formula, execution timestamp, input checksums).

### D. Secure Farmer Portal (Page 4)
- Multi-tenant, isolated portal view for agricultural landowners and authorized farmers.
- Interactive raster map viewer driven by MapLibre GL JS supporting layer switching (RGB Orthomosaic, NDVI, NDRE, GNDVI, SAVI).
- Geospatial legend rendering displaying scientific value distributions and zone classifications.
- Direct download of authorized survey deliverables and published PDF summary reports via short-lived Azure SAS URLs.
- Clear contextual messaging for surveys currently in progress or lacking specific sensor layers.

### E. Diagnostics & Actionable Insights (Page 5)
- Automated statistical summary computation per field (mean, median, standard deviation, min/max, percentile distributions).
- Zoned area breakdowns (e.g., acreage or square meters per vegetation health bracket).
- Data limitation disclosures highlighting input issues (e.g., uneven illumination, cloud shadow artifacts, lack of radiometric calibration).
- Automated generation of publication-ready, multi-page PDF summary reports using ReportLab.
- Explicit warnings on surveys where data quality precludes rigorous agronomic interpretation.

---

## 3. Strict Five-Page Restriction

To prevent scope creep and UI bloat, the application architecture is constrained to exactly five functional pages. All platform actions, views, and workflows must reside within:

1. **Page 1 — Admin Dashboard & Drone Image Ingestion** (`/admin/dashboard` or `/admin/ingestion`)
2. **Page 2 — WebODM Photogrammetry Processing** (`/admin/photogrammetry`)
3. **Page 3 — Algorithm & Multi-Map Generation** (`/admin/algorithms`)
4. **Page 4 — Secure Farmer Portal** (`/portal/surveys` or `/portal/viewer`)
5. **Page 5 — Diagnostics & Actionable Insights** (`/portal/diagnostics` or `/admin/diagnostics`)

*Ancillary Pages Allowed*:
- Minimal Authentication Gate (`/login` or `/auth`) for credentials entry.
- Technical/System Endpoints (e.g., `/healthz`, `/metrics`, API documentation `/docs` in development).

*Prohibited Pages*:
- No auxiliary sub-dashboards, separate analytics portals, marketplace directories, or standalone billing consoles.

---

## 4. Explicitly Excluded Features (Out of Scope)

The following modules and features are **explicitly excluded** from the project baseline. They must not be planned, designed, or implemented:

| Excluded Module / Feature | Rationale for Exclusion |
| :--- | :--- |
| **Marketplace & E-Commerce** | Not an agricultural marketplace; no buying/selling of drone services, inputs, or farm equipment. |
| **Billing & Payment Gateways** | Stripe, PayPal, or subscription billing integrations are strictly out of scope. |
| **Social / Community Features** | No user forums, messaging, public sharing walls, or commenting threads. |
| **Live Weather Forecasting** | Integrating weather radar or predictive microclimate models dilutes core GIS focus. |
| **Conversational Chatbots / AI Assistants**| Unnecessary overhead; standard UI controls and structured data tables provide deterministic interactions. |
| **Full Crop Management Systems (FMS)** | Platform is an aerial mapping processor, not a full Farm Management System (e.g., seed inventory, labor tracking). |
| **Automated Disease Diagnosis** | Visual multispectral reflectance cannot legally or scientifically guarantee specific pathogen/pest diagnoses without ground truthing. |
| **Chemical & Fertilizer Prescriptions** | Variable rate application (VRA) prescription maps and chemical dosage recommendations introduce regulatory and agronomic liability. |
| **Yield Prediction Models** | Accurate yield estimation requires soil samples, historical weather, cultivar genetics, and biomass models outside scope. |
| **Government / Regulatory Portal Links**| No direct submission integrations with agricultural ministries, FAA/CAA flight authorities, or subsidy databases. |
| **Native Mobile Applications** | iOS and Android native apps (Swift/Kotlin/React Native) are excluded; the frontend is a responsive web application. |

---

## 5. Rules for Approving New Requirements (Scope Change Control)

To protect the project timeline, architectural integrity, and budget, any modification to the agreed scope must adhere to the following Change Management Protocol:

1. **Formal Change Request**: Any requested feature addition or page modification must be submitted with a clear technical justification, impact assessment, and proposed revision to the Five-Page Architecture.
2. **Technical Feasibility & Constraint Check**:
   - Does it violate the Five-Page limitation?
   - Does it require non-approved cloud services (e.g., replacing Azure Blob Storage)?
   - Does it violate scientific validity (e.g., generating NDVI from 3-band RGB without NIR)?
3. **Written Approval**: No development work may commence on an out-of-scope item without explicit, written sign-off by the lead stakeholder/client.
4. **Roadmap Reprioritization**: Approved scope expansions must be accompanied by an agreed extension of deadlines or corresponding de-scoping of non-critical items.
