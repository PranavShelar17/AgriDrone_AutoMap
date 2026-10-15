# AgriDrone AutoMap — Database Architecture & Data Model
## Document Reference: `docs/phase-3/database-and-data-model.md`
**Phase**: Phase 3 — System Architecture, Technical Validation & Implementation Blueprint  
**Status**: APPROVED ARCHITECTURE BLUEPRINT  
**Version**: 1.0.0  

---

## 1. Database Philosophy & Technology Selection

The AgriDrone AutoMap persistence layer is built on **PostgreSQL 15+** with the **PostGIS 3.3+** spatial extension.

### Core Database Rules:
1. **No Binary Blob Storage in Database**: Large raster binaries (GeoTIFFs, COGs, point cloud LAS files, raw photo ZIPs) are strictly stored in Microsoft Azure Blob Storage. PostgreSQL stores structured metadata, spatial footprints, file sizes, checksums, and Azure blob URIs.
2. **Spatial Geometry as First-Class Data**: All farm boundaries, field perimeters, flight coverage extents, and orthomosaic footprints are stored as genuine PostGIS vector geometries (`GEOMETRY(Polygon, 4326)`), indexed with spatial GIST indexes.
3. **Multi-Tenant Ownership & Isolation**: Every field, survey, file, task, and map product has an explicit foreign-key path back to a `farm_id` and `user_id`. Queries in the farmer portal strictly scope access by verifying ownership.
4. **Auditable State Transitions**: All background processing tasks, photogrammetry attempts, and algorithm executions maintain immutable status ledgers with timestamps, error messages, and execution durations.

---

## 2. Entity Relationship Diagram (ERD)

```mermaid
erDiagram
    USERS ||--o{ FARMS : "owns / manages"
    USERS ||--o{ AUDIT_LOGS : "triggers"
    FARMS ||--o{ FIELDS : "contains"
    FIELDS ||--o{ SURVEYS : "covered by"
    SURVEYS ||--o{ SURVEY_FILES : "contains"
    SURVEYS ||--o{ PHOTOGRAMMETRY_TASKS : "processed by"
    SURVEYS ||--o{ MAP_PRODUCTS : "yields"
    SURVEYS ||--o{ REPORTS : "generates"
    
    PHOTOGRAMMETRY_TASKS ||--o{ TASK_LOGS : "produces"
    PHOTOGRAMMETRY_TASKS ||--o{ MAP_PRODUCTS : "generates"
    
    MAP_PRODUCTS ||--o{ ALGORITHM_JOBS : "input for"
    ALGORITHMS ||--o{ ALGORITHM_JOBS : "defines"
    ALGORITHM_JOBS ||--o{ MAP_PRODUCTS : "produces"
    
    MAP_PRODUCTS ||--o{ ZONAL_STATISTICS : "analyzed into"
    MAP_PRODUCTS ||--o{ REPORTS : "referenced in"

    USERS {
        uuid id PK
        string email UK
        string password_hash
        string full_name
        string role "ADMIN | AGRONOMIST | FARMER"
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    FARMS {
        uuid id PK
        uuid owner_id FK
        string name
        string village
        string district
        string state
        geometry boundary_geom "Polygon 4326"
        timestamp created_at
    }

    FIELDS {
        uuid id PK
        uuid farm_id FK
        string field_name
        string crop_type
        decimal area_hectares
        geometry boundary_geom "Polygon 4326"
        timestamp created_at
    }

    SURVEYS {
        uuid id PK
        uuid field_id FK
        string survey_code UK
        date flight_date
        string drone_model
        string sensor_type "RGB | MULTISPECTRAL"
        decimal flight_altitude_m
        string status "DRAFT | INGESTED | PROCESSING | COMPLETED | FAILED"
        geometry coverage_geom "Polygon 4326"
        timestamp created_at
    }

    SURVEY_FILES {
        uuid id PK
        uuid survey_id FK
        string original_filename
        string file_type "RAW_ZIP | GEOTIFF | METADATA"
        bigint file_size_bytes
        string mime_type
        string blob_uri
        string md5_checksum
        jsonb validation_metadata
        string ingestion_status "PENDING | UPLOADED | VALIDATED | REJECTED"
        timestamp created_at
    }

    PHOTOGRAMMETRY_TASKS {
        uuid id PK
        uuid survey_id FK
        string webodm_task_uuid UK
        string resolution_preset "HIGH_RES | FAST"
        boolean generate_dsm
        boolean generate_dtm
        boolean radiometric_calibration
        string status "SUBMITTED | RUNNING | COMPLETED | FAILED"
        int progress_percent
        string current_stage
        timestamp started_at
        timestamp completed_at
    }

    TASK_LOGS {
        bigserial id PK
        uuid task_id FK
        string log_level "INFO | WARNING | ERROR"
        text message
        timestamp logged_at
    }

    ALGORITHMS {
        string code PK "NDVI | NDRE | GNDVI | VARI | GLI | SAVI"
        string display_name
        string required_sensor "MULTISPECTRAL | RGB"
        jsonb formula_spec
        text description
    }

    ALGORITHM_JOBS {
        uuid id PK
        uuid input_product_id FK
        string algorithm_code FK
        jsonb parameters "L_factor, thresholds"
        string status "QUEUED | PROCESSING | COMPLETED | FAILED"
        text error_message
        timestamp started_at
        timestamp completed_at
    }

    MAP_PRODUCTS {
        uuid id PK
        uuid survey_id FK
        uuid source_task_id FK
        uuid source_job_id FK
        string product_type "ORTHOPHOTO | DSM | INDEX_NDVI | INDEX_VARI | etc"
        string blob_uri
        boolean is_cog
        int band_count
        string crs_epsg
        decimal resolution_cm_px
        geometry extent_geom "Polygon 4326"
        jsonb statistical_summary "mean, min, max, std_dev"
        boolean is_published
        timestamp created_at
    }

    ZONAL_STATISTICS {
        uuid id PK
        uuid map_product_id FK
        string zone_name "High Vigour | Moderate | Stressed | Bare Soil"
        decimal min_val
        decimal max_val
        decimal area_hectares
        decimal area_percentage
        timestamp calculated_at
    }

    REPORTS {
        uuid id PK
        uuid survey_id FK
        uuid generated_by_user_id FK
        string report_number UK
        string report_title
        string blob_uri
        bigint file_size_bytes
        string status "QUEUED | GENERATING | COMPLETED | FAILED"
        jsonb report_parameters
        timestamp created_at
    }

    AUDIT_LOGS {
        bigserial id PK
        uuid user_id FK
        string action "UPLOAD | RECONSTRUCT | COMPUTE_INDEX | DOWNLOAD_REPORT"
        string entity_type
        uuid entity_id
        inet ip_address
        text user_agent
        timestamp timestamp
    }
```

---

## 3. Detailed Table Specifications & Constraints

### 3.1. `users` Table
Stores authenticated platform identities and system roles.
- `id`: `UUID`, Primary Key, default `gen_random_uuid()`.
- `email`: `VARCHAR(255)`, Unique, Not Null, Index.
- `password_hash`: `VARCHAR(255)`, Not Null (Argon2 / Bcrypt hash).
- `full_name`: `VARCHAR(150)`, Not Null.
- `role`: `VARCHAR(30)`, Not Null, Check Constraint: `role IN ('ADMIN', 'AGRONOMIST', 'FARMER')`.
- `is_active`: `BOOLEAN`, Default `TRUE`, Not Null.
- `created_at`: `TIMESTAMPTZ`, Default `NOW()`, Not Null.

### 3.2. `farms` Table
Represents an agricultural holding or enterprise.
- `id`: `UUID`, Primary Key.
- `owner_id`: `UUID`, Foreign Key $\to$ `users(id)`, On Delete Restrict, Not Null.
- `name`: `VARCHAR(200)`, Not Null.
- `village`: `VARCHAR(100)`, Nullable.
- `district`: `VARCHAR(100)`, Nullable.
- `state`: `VARCHAR(100)`, Nullable.
- `boundary_geom`: `GEOMETRY(Polygon, 4326)`, Nullable, Spatial Index.
- `created_at`: `TIMESTAMPTZ`, Default `NOW()`, Not Null.

### 3.3. `fields` Table
Represents a discrete agricultural parcel or management zone within a farm.
- `id`: `UUID`, Primary Key.
- `farm_id`: `UUID`, Foreign Key $\to$ `farms(id)`, On Delete Cascade, Not Null.
- `field_name`: `VARCHAR(150)`, Not Null.
- `crop_type`: `VARCHAR(100)`, Nullable.
- `area_hectares`: `NUMERIC(10, 4)`, Computed from boundary or entered manually.
- `boundary_geom`: `GEOMETRY(Polygon, 4326)`, Not Null, Spatial Index.

### 3.4. `surveys` Table
Represents a specific aerial flight survey conducted over a field.
- `id`: `UUID`, Primary Key.
- `field_id`: `UUID`, Foreign Key $\to$ `fields(id)`, On Delete Cascade, Not Null.
- `survey_code`: `VARCHAR(50)`, Unique, Not Null (e.g., `SRV-2026-BAR-001`).
- `flight_date`: `DATE`, Not Null.
- `drone_model`: `VARCHAR(100)`, Nullable.
- `sensor_type`: `VARCHAR(50)`, Not Null, Check: `sensor_type IN ('RGB', 'MULTISPECTRAL')`.
- `flight_altitude_m`: `NUMERIC(6, 2)`, Nullable.
- `status`: `VARCHAR(30)`, Not Null, Default `'DRAFT'`, Check: `status IN ('DRAFT', 'INGESTED', 'PROCESSING', 'COMPLETED', 'FAILED')`.
- `coverage_geom`: `GEOMETRY(Polygon, 4326)`, Nullable, Spatial Index.

### 3.5. `survey_files` Table (Page 1)
Maintains the registry of raw uploaded archives, images, and pre-stitched GeoTIFFs.
- `id`: `UUID`, Primary Key.
- `survey_id`: `UUID`, Foreign Key $\to$ `surveys(id)`, On Delete Cascade, Not Null.
- `original_filename`: `VARCHAR(255)`, Not Null.
- `file_type`: `VARCHAR(50)`, Not Null, Check: `file_type IN ('RAW_ZIP', 'GEOTIFF', 'METADATA')`.
- `file_size_bytes`: `BIGINT`, Not Null.
- `mime_type`: `VARCHAR(100)`, Not Null.
- `blob_uri`: `VARCHAR(500)`, Not Null (Azure storage path).
- `md5_checksum`: `VARCHAR(32)`, Nullable.
- `validation_metadata`: `JSONB`, Nullable (stores EXIF count, geotransform, CRS, resolution).
- `ingestion_status`: `VARCHAR(30)`, Not Null, Default `'PENDING'`, Check: `ingestion_status IN ('PENDING', 'UPLOADED', 'VALIDATED', 'REJECTED')`.

### 3.6. `photogrammetry_tasks` & `task_logs` Tables (Page 2)
Tracks WebODM 3D reconstruction and orthomosaic generation jobs.
- `id`: `UUID`, Primary Key.
- `survey_id`: `UUID`, Foreign Key $\to$ `surveys(id)`, On Delete Cascade, Not Null.
- `webodm_task_uuid`: `VARCHAR(64)`, Unique, Nullable.
- `resolution_preset`: `VARCHAR(30)`, Default `'HIGH_RES'`.
- `generate_dsm`: `BOOLEAN`, Default `TRUE`.
- `generate_dtm`: `BOOLEAN`, Default `TRUE`.
- `radiometric_calibration`: `BOOLEAN`, Default `FALSE`.
- `status`: `VARCHAR(30)`, Not Null, Default `'SUBMITTED'`, Check: `status IN ('SUBMITTED', 'DISPATCHING', 'RUNNING', 'COMPLETED', 'FAILED')`.
- `progress_percent`: `INTEGER`, Default `0`, Check: `progress_percent BETWEEN 0 AND 100`.
- `current_stage`: `VARCHAR(100)`, Nullable (e.g. `'Point Cloud Densification'`).
- `started_at`: `TIMESTAMPTZ`, Nullable.
- `completed_at`: `TIMESTAMPTZ`, Nullable.

### 3.7. `map_products` Table (Pages 2, 3, 4)
The authoritative catalog of all raster products (Orthomosaics, DSMs, COG index layers).
- `id`: `UUID`, Primary Key.
- `survey_id`: `UUID`, Foreign Key $\to$ `surveys(id)`, On Delete Cascade, Not Null.
- `source_task_id`: `UUID`, Foreign Key $\to$ `photogrammetry_tasks(id)`, Nullable.
- `source_job_id`: `UUID`, Foreign Key $\to$ `algorithm_jobs(id)`, Nullable.
- `product_type`: `VARCHAR(50)`, Not Null, Check: `product_type IN ('ORTHOPHOTO', 'DSM', 'DTM', 'INDEX_NDVI', 'INDEX_NDRE', 'INDEX_GNDVI', 'INDEX_VARI', 'INDEX_GLI', 'INDEX_SAVI')`.
- `blob_uri`: `VARCHAR(500)`, Not Null.
- `is_cog`: `BOOLEAN`, Default `TRUE` (Must be Cloud-Optimized GeoTIFF).
- `band_count`: `INTEGER`, Not Null.
- `crs_epsg`: `VARCHAR(20)`, Not Null (e.g. `'EPSG:32643'`).
- `resolution_cm_px`: `NUMERIC(8, 2)`, Nullable.
- `extent_geom`: `GEOMETRY(Polygon, 4326)`, Not Null, Spatial Index.
- `statistical_summary`: `JSONB`, Nullable (stores `{min: -0.2, max: 0.85, mean: 0.48, std_dev: 0.14}`).
- `is_published`: `BOOLEAN`, Default `FALSE` (Governs visibility in Farmer Portal).

### 3.8. `algorithm_jobs` Table (Page 3)
Tracks vegetation index calculations executed by Celery workers via GDAL/Rasterio/NumPy.
- `id`: `UUID`, Primary Key.
- `input_product_id`: `UUID`, Foreign Key $\to$ `map_products(id)`, On Delete Restrict, Not Null.
- `algorithm_code`: `VARCHAR(30)`, Foreign Key $\to$ `algorithms(code)`, Not Null.
- `parameters`: `JSONB`, Nullable (e.g. `{"L_factor": 0.5}`).
- `status`: `VARCHAR(30)`, Not Null, Default `'QUEUED'`, Check: `status IN ('QUEUED', 'PROCESSING', 'COMPLETED', 'FAILED')`.
- `error_message`: `TEXT`, Nullable.

### 3.9. `reports` Table (Page 5)
Maintains compiled agronomic PDF reports generated by ReportLab.
- `id`: `UUID`, Primary Key.
- `survey_id`: `UUID`, Foreign Key $\to$ `surveys(id)`, On Delete Cascade, Not Null.
- `generated_by_user_id`: `UUID`, Foreign Key $\to$ `users(id)`, Not Null.
- `report_number`: `VARCHAR(50)`, Unique, Not Null (e.g. `RPT-2026-10-0012`).
- `report_title`: `VARCHAR(200)`, Not Null.
- `blob_uri`: `VARCHAR(500)`, Not Null.
- `file_size_bytes`: `BIGINT`, Not Null.
- `status`: `VARCHAR(30)`, Not Null, Check: `status IN ('QUEUED', 'GENERATING', 'COMPLETED', 'FAILED')`.
- `report_parameters`: `JSONB`, Nullable.

---

## 4. Indexing Strategy

To ensure high performance across complex multi-tenant filters and spatial queries:
1. **Spatial Indexes (GIST)**:
   - `CREATE INDEX idx_fields_boundary_geom ON fields USING GIST (boundary_geom);`
   - `CREATE INDEX idx_surveys_coverage_geom ON surveys USING GIST (coverage_geom);`
   - `CREATE INDEX idx_map_products_extent_geom ON map_products USING GIST (extent_geom);`
2. **Foreign Key & Tenant B-Tree Indexes**:
   - `CREATE INDEX idx_farms_owner_id ON farms (owner_id);`
   - `CREATE INDEX idx_fields_farm_id ON fields (farm_id);`
   - `CREATE INDEX idx_surveys_field_id ON surveys (field_id);`
   - `CREATE INDEX idx_survey_files_survey_id ON survey_files (survey_id);`
   - `CREATE INDEX idx_map_products_survey_id ON map_products (survey_id);`
   - `CREATE INDEX idx_reports_survey_id ON reports (survey_id);`
3. **Compound Status & Lifecycle Indexes**:
   - `CREATE INDEX idx_tasks_survey_status ON photogrammetry_tasks (survey_id, status);`
   - `CREATE INDEX idx_algo_jobs_status ON algorithm_jobs (status);`
   - `CREATE INDEX idx_products_published ON map_products (survey_id, is_published);`

---

## 5. Database Migration Strategy (Alembic)

Database schema evolution is managed through **Alembic**:
1. All migrations are tracked in `backend/alembic/versions/` with sequential revision IDs.
2. The initial migration `0001_initial_schema.py` enables PostGIS (`CREATE EXTENSION IF NOT EXISTS postgis;`) and sets up all core tables, constraints, and GIST indexes.
3. Migrations are executed automatically in container entrypoints during staging/production deployment via `alembic upgrade head`.
4. Downward migrations (`downgrade()`) are mandatory for every revision to support rollback.
