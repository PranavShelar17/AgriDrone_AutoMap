# AgriDrone AutoMap — Environment Configuration & Secret Management
## Document Reference: `docs/phase-4/environment-configuration.md`
**Phase**: Phase 4 — Platform Foundation, Database Setup, Backend/Frontend Skeleton & Initial Testing  
**Status**: APPROVED CONFIGURATION GUIDE  
**Version**: 1.0.0  

---

## 1. Environment Variable Inventory & Specifications

The following table documents all environment variables defined in [`backend/.env.example`](file:///c:/Users/Admin/Desktop/new%20dron%202/backend/.env.example) and parsed by [`backend/app/core/config.py`](file:///c:/Users/Admin/Desktop/new%20dron%202/backend/app/core/config.py):

| Variable Name | Required? | Default Value | Purpose & Scope | Security Classification |
| :--- | :---: | :--- | :--- | :--- |
| **`ENVIRONMENT`** | Yes | `development` | Dictates debug mode, logging verbosity, and error stack trace formatting (`development`, `staging`, `production`). | Public |
| **`PROJECT_NAME`** | No | `AgriDrone AutoMap` | Application display name in OpenAPI documentation. | Public |
| **`API_V1_STR`** | No | `/api/v1` | URL prefix for versioned REST API endpoints. | Public |
| **`SECRET_KEY`** | Yes | `dev_insecure_secret_key...` | Cryptographic key used to sign JWT session tokens and hash payloads. Must be 32+ random characters in production. | **CONFIDENTIAL (Secret)** |
| **`DATABASE_URL`** | Yes | `postgresql://agridrone_user:local_pass@localhost:5434/agridrone_db` | Connection string for PostgreSQL with PostGIS. Automatically normalized to `postgresql+psycopg2://` driver dialect. | **RESTRICTED (Credentials)** |
| **`DB_POOL_SIZE`** | No | `10` | Number of persistent connections maintained in SQLAlchemy connection pool. | Internal Config |
| **`DB_MAX_OVERFLOW`**| No | `20` | Maximum temporary connections permitted beyond `DB_POOL_SIZE`. | Internal Config |
| **`DB_TIMEOUT_SECONDS`**| No | `5` | Socket connect timeout in seconds before failing fast. | Internal Config |
| **`REDIS_URL`** | Yes | `redis://localhost:6380/0` | Connection string for Redis broker used by Celery task queues. | Internal Config |
| **`CORS_ORIGINS`** | Yes | `["http://localhost:3000","http://localhost:3005"]` | List of allowed HTTP browser origins permitted by CORS middleware. | Public Config |
| **`LOG_LEVEL`** | No | `INFO` | Logging threshold (`DEBUG`, `INFO`, `WARNING`, `ERROR`). | Public Config |

---

## 2. Planned Future Configuration (Phase 5+)

These variables are defined in the schema and architecture, but remain dormant during Phase 4:

| Variable Name | Planned Phase | Purpose | Notes |
| :--- | :---: | :--- | :--- |
| **`AZURE_STORAGE_CONNECTION_STRING`** | Phase 5 | Azure Storage connection credentials for local dev | Left empty when Managed Identity is active in production. |
| **`AZURE_STORAGE_ACCOUNT_NAME`** | Phase 5 | Target Azure Blob storage account | Default: `agridronestorage` |
| **`AZURE_CONTAINER_*`** | Phase 5 | Logical container names (`raw-surveys`, `orthomosaics`, etc.) | Configures target binary storage buckets. |
| **`WEBODM_API_URL`** | Phase 6 | WebODM / NodeODM photogrammetry orchestrator endpoint | Default: `http://localhost:3001` (or `http://nodeodm:3000` in Docker). |

---

## 3. Frontend Configuration Variables

All frontend configuration is isolated in [`frontend/lib/config.ts`](file:///c:/Users/Admin/Desktop/new%20dron%202/frontend/lib/config.ts):

| Variable Name | Default Value | Client-Exposed? | Purpose |
| :--- | :--- | :---: | :--- |
| **`NEXT_PUBLIC_API_URL`** | `http://localhost:8005/api/v1` | **Yes (Browser)** | Base HTTP URL used by the Next.js API client to communicate with FastAPI. |

### Strict Client Isolation Rules:
- **No Private Keys in `NEXT_PUBLIC_`**: Database passwords, Redis URLs, and Azure master keys are **strictly forbidden** from being prefixed with `NEXT_PUBLIC_`.
- Only public-facing REST endpoints and client-safe feature flags may be exposed in browser bundles.

---

## 4. Secret Governance & Git Safeguards

1. **`.gitignore` Enforcement**: The repository root `.gitignore` explicitly ignores `.env`, `.env.local`, and `*.env` files.
2. **Placeholder Integrity**: `.env.example` contains only benign sample credentials (`local_pass`, `dev_insecure_secret_key...`). Production keys are injected via CI/CD secrets (GitHub Secrets / Azure Key Vault).
