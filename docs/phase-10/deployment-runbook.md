# Production Deployment Runbook & Operator Guide

**Document:** Operational Runbook & Deployment Guide  
**Phase:** Phase 10  
**Target Audience:** DevOps Engineers, Cloud Operators, System Administrators  
**Date:** October 2026  

---

## 1. Prerequisites & Required Tools

Before initiating deployment, verify that the host machine meets these minimum requirements:

- **Operating System:** Linux (Ubuntu 22.04 LTS / Debian 12 recommended) or Windows Server with WSL2.
- **Hardware:** Minimum 4 CPU cores, 16 GB RAM (32 GB recommended for heavy WebODM jobs), 100 GB NVMe/SSD storage.
- **Software Installed:**
  - Docker Engine `v24.0+`
  - Docker Compose `v2.20+`
  - Git `v2.40+`
  - (Optional for non-containerized dev) Python `3.11+` and Node.js `20.x LTS`

---

## 2. Step-by-Step Deployment Procedure

### Step 1: Clone Repository & Create Environment Configuration
```bash
git clone https://github.com/your-org/agridrone-automap.git
cd agridrone-automap

# Copy environment template
cp .env.example .env
```

### Step 2: Configure Production Secrets
Edit `.env` using your preferred text editor (e.g. `nano .env`):
```ini
# Generate a cryptographically secure 64-character secret:
# In terminal run: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=paste_your_generated_64_char_hex_secret_here

# Set production environment
ENVIRONMENT=production
COOKIE_SECURE=true
CORS_ORIGINS=["https://yourdomain.com"]

# Set secure database credentials
POSTGRES_DB=agridrone_db
POSTGRES_USER=agridrone_admin
POSTGRES_PASSWORD=generate_a_strong_database_password_here

# Azure Blob Storage (or leave empty to use local dev storage)
AZURE_STORAGE_CONNECTION_STRING=your_azure_storage_connection_string_here
AZURE_STORAGE_ACCOUNT_NAME=your_storage_account_name

# Frontend Public API URL
NEXT_PUBLIC_API_URL=https://yourdomain.com/api/v1
```

### Step 3: Launch Production Containers
```bash
# Build and start all services in detached mode
docker compose -f docker-compose.prod.yml up -d --build

# Verify container statuses
docker compose -f docker-compose.prod.yml ps
```

### Step 4: Run Database Migrations
Apply all PostGIS database migrations to the running database container:
```bash
docker exec -it agridrone_prod_backend alembic upgrade head
```
*Expected Output:* `Running upgrade ... -> 003_algorithms_phase7`

### Step 5: Seed Default Administrative Accounts
```bash
docker exec -it agridrone_prod_backend python scripts/seed_phase9_users.py
```

---

## 3. Smoke Testing & Verification

Execute these verification commands immediately after deployment:

### 1. Liveness Probe
```bash
curl -f http://localhost:8005/api/v1/health
```
*Expected:* `{"status":"ok","version":"0.1.0","environment":"production"}`

### 2. Readiness Probe (Checks PostgreSQL PostGIS & Redis)
```bash
curl -f http://localhost:8005/api/v1/health/readiness
```
*Expected:* `{"status":"ready","components":{"database":{"status":"healthy",...},"redis":{"status":"healthy",...}}}`

### 3. Frontend Web Verification
Open `http://localhost:3005` in your browser. Verify that the login page loads and test sign-in using `admin@agridrone.local`.

---

## 4. Rollback & Recovery Procedures

If a deployment encounters critical runtime defects:

### Container Rollback
```bash
# Revert to previous Git release tag
git checkout v1.0.0-rc1

# Re-deploy previous stable container images
docker compose -f docker-compose.prod.yml up -d --build
```

### Database Migration Rollback (If needed)
```bash
# Downgrade database schema by 1 revision
docker exec -it agridrone_prod_backend alembic downgrade -1
```

---

## 5. Troubleshooting Common Failures

| Issue | Root Cause | Solution |
| :--- | :--- | :--- |
| **Port Collision (5434 / 6380)** | Another local Postgres/Redis process is bound to the port. | Modify host ports in `docker-compose.prod.yml` or stop conflicting services (`sudo systemctl stop postgresql`). |
| **Readiness probe returns 503** | Database container is still initializing or PostGIS extension missing. | Wait 15 seconds; verify logs with `docker logs agridrone_prod_db`. |
| **Photogrammetry job fails** | NodeODM container ran out of memory. | Allocate more RAM in Docker Desktop / host OS (minimum 8GB for 100+ photo sets). |
| **CORS errors in browser** | `CORS_ORIGINS` in `.env` does not match the frontend URL. | Add your exact protocol and domain to `CORS_ORIGINS` in `.env` and restart backend (`docker restart agridrone_prod_backend`). |
