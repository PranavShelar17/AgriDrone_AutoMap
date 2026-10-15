# Hosting & Production Deployment Decision ADR

**Document:** ADR-010-HOSTING  
**Status:** Pending User Approval  
**Date:** October 2026  
**Context:** AgriDrone AutoMap Phase 10 Production Deployment Target  

---

## 1. Context & Hosting Requirements

AgriDrone AutoMap is a multi-tier geospatial system that cannot be deployed on a frontend-only platform like static Vercel. Hosting infrastructure must accommodate:

1. **Frontend:** Next.js 14 App Router (Node.js SSR + Static Optimization).
2. **Backend API:** FastAPI Python ASGI process requiring GDAL/GEOS C-libraries for spatial coordinate math.
3. **Database:** PostgreSQL 16 with native **PostGIS 3.4** extension enabled for geospatial bounding box and polygon operations.
4. **Task Broker & Queues:** Redis 7.2 + Celery worker pool for background orthomosaic processing and vegetation index raster math.
5. **Photogrammetry Compute:** WebODM/NodeODM requiring substantial multi-core CPU and memory allocations during 3D point cloud reconstruction.
6. **Object Storage:** Microsoft Azure Blob Storage (existing approved primary storage provider).

---

## 2. Evaluated Hosting Options

### Option 1: Microsoft Azure Unified Cloud Architecture (Recommended for Enterprise)
- **Frontend & API:** Azure Container Apps (ACA) or Azure App Service for Linux.
- **Database:** Azure Database for PostgreSQL — Flexible Server (with PostGIS extension enabled).
- **Cache/Broker:** Azure Cache for Redis.
- **Worker:** Azure Container Apps background replica pool (auto-scales based on Celery queue length).
- **Storage:** Azure Blob Storage (General Purpose v2 with hot/cool tiers).
- **Pros:**
  - Zero egress costs between API, database, and Azure Blob Storage.
  - Native PostGIS support in Flexible Server.
  - Unified security: Managed Identities (MSI) eliminate hardcoded storage secrets.
  - Integrated Azure Monitor, Application Insights, and log analytics.
- **Cons:**
  - Requires active Azure subscription and cloud budget.

### Option 2: Hybrid Cloud Architecture (Vercel + Managed Cloud)
- **Frontend:** Vercel Pro (Next.js App Router).
- **Backend & Worker:** DigitalOcean App Platform / Render / AWS ECS.
- **Database:** Neon / Supabase / AWS RDS PostgreSQL (with PostGIS).
- **Storage:** Microsoft Azure Blob Storage.
- **Pros:**
  - Industry-standard Next.js edge performance on Vercel.
- **Cons:**
  - Cross-cloud network latency between Vercel frontend, AWS/DigitalOcean backend, and Azure Blob Storage.
  - Fragmented billing across three separate cloud vendors.
  - High cloud egress charges when streaming high-resolution raster tiles from Azure through third-party APIs.

### Option 3: Self-Hosted / On-Premise Edge Deployment (Recommended for Local / Offline Farms)
- **Orchestration:** Single or clustered Linux servers running Docker Compose or lightweight Kubernetes (K3s).
- **Database & Services:** Containerized PostgreSQL 16 + PostGIS 3.4 and Redis 7.2.
- **Storage:** Local NVMe disk storage with periodic automated sync to Azure Blob Storage when network is available.
- **Pros:**
  - $0 ongoing cloud compute fees.
  - Completely operational in remote rural farming regions without broadband Internet connectivity.
  - Eliminates cloud upload delays for large 10GB+ raw drone surveys.
- **Cons:**
  - Requires customer-managed physical hardware, power backups, and manual OS maintenance.

---

## 3. Decision Matrix

| Evaluation Criteria | Option 1: Azure Unified | Option 2: Hybrid Cloud | Option 3: Self-Hosted Edge |
| :--- | :---: | :---: | :---: |
| **Operational Simplicity** | **High** (Single console) | Low (Fragmented vendors) | Medium (Docker management) |
| **Network Egress Costs** | **$0** (Co-located in region)| High (Cross-cloud bandwidth) | **$0** (Local LAN) |
| **Offline Capability** | Low (Internet required) | Low (Internet required) | **Full Offline Support** |
| **Photogrammetry Speed** | High (Scalable cloud VMs) | Medium | Fast (Local hardware) |
| **Enterprise Governance** | **SOC2, ISO, HIPAA ready**| Complex auditing | Physical security dependent |

---

## 4. Formal Recommendation & Approval Gate

**Recommendation:**
- For cloud SaaS delivery: **Option 1 (Microsoft Azure Unified Architecture)**.
- For regional agricultural cooperatives or private flight operators: **Option 3 (Docker Compose / Edge)** using the provided `docker-compose.prod.yml`.

---

> [!IMPORTANT]
> **MANDATORY APPROVAL GATE:**
> In strict compliance with Section 11 of the Master Prompt:
> **No cloud hosting provider has been automatically provisioned, no DNS records have been modified, and no paid cloud resources have been created.**
> Cloud provisioning and domain configuration will proceed only upon your explicit approval and selection of the preferred hosting tier.
