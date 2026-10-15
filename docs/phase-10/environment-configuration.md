# Environment Configuration Standard & Variable Reference

**Document:** Environment Variables & Configuration Specification  
**Phase:** Phase 10  
**Status:** Approved  
**Date:** October 2026  

---

## 1. Environment Profiles Overview

AgriDrone AutoMap supports four distinct environment tiers:
1. **Local Development (`development`):** Local Postgres (port 5434), local Redis (port 6380), local storage fallback enabled, verbose logging.
2. **Automated Testing (`testing`):** Isolated test database fixtures, mock WebODM endpoints, fast execution mode.
3. **Staging (`staging`):** Exact containerized replica of production, pre-production Azure storage containers, HTTPS enabled.
4. **Production (`production`):** Hardened secrets, `COOKIE_SECURE=true`, restricted CORS origins, managed cloud Postgres and Redis, Azure Blob Storage with immutability.

---

## 2. Configuration Variables Matrix

| Variable Name | Required Tier | Default / Example Value | Description & Security Policy |
| :--- | :---: | :--- | :--- |
| `ENVIRONMENT` | All | `production` | Deployment mode: `development`, `staging`, `production`. |
| `PROJECT_NAME` | All | `"AgriDrone AutoMap"` | Display name for API and OpenAPI schema. |
| `API_V1_STR` | All | `/api/v1` | URL prefix for versioned REST API endpoints. |
| `SECRET_KEY` | **Prod Required** | *Generated 64-char hex* | **CRITICAL:** Signing key for HS256 JWT tokens. Must be minimum 32 chars. |
| `DATABASE_URL` | **Prod Required** | `postgresql://user:pass@host:5432/db` | Connection string for PostgreSQL + PostGIS database. |
| `DB_POOL_SIZE` | Prod | `20` | Maximum persistent database connections in pool. |
| `DB_MAX_OVERFLOW` | Prod | `30` | Maximum temporary overflow connections during peak spikes. |
| `REDIS_URL` | **Prod Required** | `redis://redis:6379/0` | Connection URI for Redis task queue broker and cache. |
| `CORS_ORIGINS` | **Prod Required** | `["https://app.agridrone.com"]` | JSON array of trusted frontend domains allowed for CORS. |
| `JWT_ALGORITHM` | All | `HS256` | Cryptographic algorithm for JWT signatures. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | All | `480` | Lifespan of session tokens (8 hours). |
| `COOKIE_SECURE` | Prod | `true` | Enforces that session cookies are transmitted over HTTPS only. |
| `COOKIE_SAMESITE` | All | `lax` | CSRF defense policy: `lax`, `strict`, or `none`. |
| `AUTH_RATE_LIMIT_PER_MINUTE` | All | `20` | Maximum login attempts per IP per 60 seconds. |
| `AZURE_STORAGE_CONNECTION_STRING` | Prod | `DefaultEndpointsProtocol=https;...` | Azure Blob Storage primary connection secret. |
| `AZURE_STORAGE_ACCOUNT_NAME` | Prod | `agridronestorage` | Storage account identifier. |
| `AZURE_CONTAINER_RAW` | All | `raw-surveys` | Container for original uploaded drone JPEG/TIFF photos. |
| `AZURE_CONTAINER_ORTHO` | All | `orthomosaics` | Container for 2D orthophotos and DSM elevation models. |
| `AZURE_CONTAINER_INDICES` | All | `vegetation-indices` | Container for Cloud-Optimized GeoTIFF index products. |
| `AZURE_CONTAINER_REPORTS` | All | `reports` | Container for generated PDF agronomic reports. |
| `ALLOW_DEV_LOCAL_STORAGE` | Dev only | `false` in production | If true, permits fallback storage to `backend/storage/`. |
| `MAX_UPLOAD_SIZE_BYTES` | All | `524288000` | Maximum permitted file upload size (500 MB). |
| `WEBODM_API_URL` | All | `http://nodeodm:3000` | REST API URL for NodeODM photogrammetry processing node. |
| `WEBODM_TIMEOUT_SECONDS` | All | `30` | HTTP timeout when communicating with WebODM. |
| `NEXT_PUBLIC_API_URL` | Frontend | `https://api.agridrone.com/api/v1` | Public backend API URL consumed by client browser. |

---

## 3. Strict Security Rules

1. **Server Secrets in Frontend:** Under no circumstances may `SECRET_KEY`, `DATABASE_URL`, or `AZURE_STORAGE_CONNECTION_STRING` be prefixed with `NEXT_PUBLIC_`.
2. **Version Control Exclusion:** The `.env` file is strictly ignored by `.gitignore`. Only `.env.example` with documented placeholder strings may be checked into Git.
3. **Startup Validation:** The FastAPI backend verifies that `SECRET_KEY` is not using default development placeholders when `ENVIRONMENT == "production"`.
