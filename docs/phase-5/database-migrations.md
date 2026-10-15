# AgriDrone AutoMap — Phase 5 Database Schema & Migrations
## Document Reference: `docs/phase-5/database-migrations.md`
**Phase**: Phase 5 — Admin Dashboard, Farm/Survey Management & Drone Image Ingestion  
**Status**: APPROVED SCHEMA ALIGNMENT  
**Version**: 1.0.0  

---

## 1. Migration History & Status

The database schema is managed via **Alembic** under `backend/alembic/`.

| Revision ID | Description | Created Date | Status |
| :--- | :--- | :--- | :--- |
| **`001_initial_core_schema`** | Baseline schema with PostGIS extension, users, farms, fields, surveys, survey_files, photogrammetry tasks, algorithms, map products, zonal statistics, reports, audit logs. | 2026-10-14 | **Applied & Head** |

Verification command:
```powershell
cd backend
.\.venv\Scripts\alembic.exe current
# Output: 001_initial_core_schema (head)
```

---

## 2. Phase 5 Entities Utilized

Phase 5 directly operates on the following core database tables created by migration `001_initial_core_schema.py`:

### 1. `users` Table
- Stores platform user accounts and roles (`ADMIN`, `AGRONOMIST`, `FARMER`).
- In Phase 5 development mode, automatically provisions the default administrator record: `admin@agridrone.local`.

### 2. `farms` Table
- `id` (`UUID`, PK)
- `owner_id` (`UUID`, FK to `users.id`)
- `name` (`VARCHAR(200)`, NOT NULL)
- `village`, `district`, `state` (`VARCHAR(100)`)
- `boundary_geom` (`GEOMETRY(POLYGON, 4326)`)
- `created_at` (`TIMESTAMPTZ`)

### 3. `fields` Table
- `id` (`UUID`, PK)
- `farm_id` (`UUID`, FK to `farms.id`, ON DELETE CASCADE)
- `field_name` (`VARCHAR(150)`, NOT NULL)
- `crop_type` (`VARCHAR(100)`)
- `area_hectares` (`NUMERIC(10, 4)`)
- `boundary_geom` (`GEOMETRY(POLYGON, 4326)`)
- `created_at` (`TIMESTAMPTZ`)

### 4. `surveys` Table
- `id` (`UUID`, PK)
- `field_id` (`UUID`, FK to `fields.id`, ON DELETE CASCADE)
- `survey_code` (`VARCHAR(50)`, UNIQUE, NOT NULL)
- `flight_date` (`DATE`, NOT NULL)
- `drone_model` (`VARCHAR(100)`)
- `sensor_type` (`VARCHAR(50)`, default `'RGB'`)
- `flight_altitude_m` (`NUMERIC(6, 2)`)
- `status` (`VARCHAR(30)`, default `'DRAFT'`)
- `coverage_geom` (`GEOMETRY(POLYGON, 4326)`)
- `created_at` (`TIMESTAMPTZ`)

### 5. `survey_files` Table
- `id` (`UUID`, PK)
- `survey_id` (`UUID`, FK to `surveys.id`, ON DELETE CASCADE)
- `original_filename` (`VARCHAR(255)`, NOT NULL)
- `file_type` (`VARCHAR(50)`, e.g. `'RAW_IMAGE'`, `'GEOTIFF'`, `'RAW_ZIP'`)
- `file_size_bytes` (`BIGINT`, NOT NULL)
- `mime_type` (`VARCHAR(100)`, NOT NULL)
- `blob_uri` (`VARCHAR(500)`, NOT NULL)
- `md5_checksum` (`VARCHAR(32)`)
- `validation_metadata` (`JSONB`, contains parsed EXIF, GPS, CRS, bands, errors)
- `ingestion_status` (`VARCHAR(30)`, `'VALIDATED'` or `'REJECTED'`)
- `created_at` (`TIMESTAMPTZ`)
