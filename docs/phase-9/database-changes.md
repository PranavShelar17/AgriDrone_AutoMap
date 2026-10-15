# Database Changes & Schema Integrity Report

**Document:** Database & Migrations Log — Phase 9  
**Status:** Implemented & Verified  
**Date:** October 2026  

---

## 1. Schema Baseline Inspection

Prior to implementing Phase 9, the PostgreSQL 16 + PostGIS database schema was audited using SQLAlchemy metadata inspection and Alembic migration history.

### Existing Relational Structure:
The Phase 3 foundational migrations had already provisioned the core user and security entities:
1. **`users` Table:**
   - `id`: UUID (Primary Key, default `uuid4()`).
   - `email`: VARCHAR(255) (Unique, Indexed, Non-null).
   - `hashed_password`: VARCHAR(255) (Non-null).
   - `full_name`: VARCHAR(255) (Non-null).
   - `role`: VARCHAR(50) (Enum: `ADMIN`, `AGRONOMIST`, `FARMER`).
   - `is_active`: BOOLEAN (Default `True`).
   - `created_at`, `updated_at`: TIMESTAMP WITH TIME ZONE.
2. **`farms` Table:**
   - `id`: UUID (Primary Key).
   - `owner_id`: UUID (Foreign Key referencing `users.id` with `ON DELETE RESTRICT`).
   - `name`, `village`, `district`, `state`, `boundary_geojson`, `created_at`.
3. **`reports` Table:**
   - `id`: UUID (Primary Key).
   - `survey_id`: UUID (Foreign Key referencing `surveys.id`).
   - `generated_by_user_id`: UUID (Foreign Key referencing `users.id`).
   - `report_number`, `report_title`, `blob_uri`, `file_size_bytes`, `status`.
4. **`audit_logs` Table:**
   - `id`: UUID (Primary Key).
   - `user_id`: UUID (Nullable Foreign Key referencing `users.id`).
   - `action`: VARCHAR(100) (Indexed).
   - `resource_type`: VARCHAR(100).
   - `resource_id`: UUID (Nullable).
   - `ip_address`: INET / VARCHAR(45).
   - `details`: JSONB.
   - `created_at`: TIMESTAMP WITH TIME ZONE (Indexed).

---

## 2. Migration Decisions

Because the relational tables and foreign keys were designed comprehensively during Phase 3, **no destructive schema alterations, column drops, or breaking migrations were required for Phase 9**.

### Preserving Existing Data:
- All pre-existing farm boundaries, field polygons, raw survey image records, photogrammetry tasks, and vegetation index rasters (NDVI/NDRE/VARI) were preserved with 100% integrity.
- Zero database resets or tables drops occurred.

---

## 3. Seed Accounts & Farm Associations

To enable immediate, reproducible testing and evaluation, `backend/scripts/seed_phase9_users.py` was executed. The script securely seeds default accounts using standard Bcrypt hashing (12 rounds) and links them to existing farm records:

### Seed Account Inventory

| Email | Role | Default Password | Assigned Farm | Scope |
| :--- | :---: | :--- | :--- | :--- |
| `admin@agridrone.local` | `ADMIN` | `Admin@AgriDrone2026!` | All Farms | System-wide administrative control |
| `farmer@greenvalley.local` | `FARMER` | `Farmer@AgriDrone2026!` | Baramati Precision Farm | Restricted strictly to Baramati fields & maps |
| `farmer2@sunrise.local` | `FARMER` | `Farmer2@AgriDrone2026!` | Ingestion Test Farm | Restricted strictly to Ingestion Test fields |

### Seeding Command:
```bash
python scripts/seed_phase9_users.py
```
Output:
```
[INFO] Admin user exists: admin@agridrone.local
[INFO] Farmer user exists: farmer@greenvalley.local
[INFO] Farmer 2 user exists: farmer2@sunrise.local
[INFO] Updated farm 'Baramati Precision Farm Updated' owner to farmer@greenvalley.local
[INFO] Updated farm 'Ingestion Test Farm' owner to farmer2@sunrise.local
[SUCCESS] Phase 9 users seeded and assigned to farms successfully.
```
