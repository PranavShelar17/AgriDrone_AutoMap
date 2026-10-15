# AgriDrone AutoMap — Phase 3 Open Technical Decisions
## Document Reference: `docs/phase-3/phase-3-open-decisions.md`
**Phase**: Phase 3 — System Architecture, Technical Validation & Implementation Blueprint  
**Status**: APPROVED ARCHITECTURE BLUEPRINT  
**Version**: 1.0.0  

---

## 1. Registry of Open Technical Decisions

The following items represent architectural or operational decisions that remain open. None of these items block Phase 4 foundation setup, as the system architecture provides decoupled abstraction layers for each. However, each decision must be formally ratified before its designated phase deadline.

---

### Decision 1: Production Authentication & Identity Provider (IdP)
- **Current Status**: UNDECIDED (Decoupled `AuthManager` interface with Bearer JWT mock tokens used for development).
- **Options Under Consideration**:
  1. *Option A (Self-Hosted PostgreSQL JWT Auth)*: Direct email/password authentication using Argon2/Bcrypt password hashing and FastAPI JWT generation. Minimal external dependencies, zero third-party licensing cost.
  2. *Option B (Microsoft Entra ID / Azure AD B2C)*: Native enterprise single sign-on (SSO) and social login integrated with Azure cloud ecosystem. High compliance and MFA support, but introduces external cloud identity dependency.
  3. *Option C (Managed OIDC / Auth0 / Clerk)*: Turnkey developer identity service with pre-built login widgets.
- **Why It Matters**: Dictates whether password resets, multi-factor authentication, and session tokens are stored in the platform's PostgreSQL database or delegated to an external identity provider.
- **Dependencies**: Frontend auth layout, user database schema migrations.
- **Resolution Deadline**: **Phase 7 (Farmer Portal & Access Control Implementation)**.

---

### Decision 2: Raster Tile Serving Infrastructure (TiTiler vs Client-Side COG)
- **Current Status**: PROPOSED (Option A: TiTiler / FastAPI dynamic tile endpoint recommended).
- **Options Under Consideration**:
  1. *Option A (Dynamic Backend Tile Endpoint)*: A FastAPI endpoint powered by `rasterio` / `rio-tiler` reads the COG in Azure Blob Storage via HTTP range requests, applies the colormap server-side, and returns $256 \times 256$ PNG tiles. Compatible with all mobile devices and browsers.
  2. *Option B (Pure Client-Side geotiff.js WebGL)*: MapLibre fetches COG byte ranges directly from Azure via SAS and computes colormaps using WebGL fragment shaders in JavaScript. Zero server compute, but risks performance degradation on low-tier farmer smartphones.
- **Why It Matters**: Impacts server CPU/RAM utilization versus client mobile browser rendering performance.
- **Dependencies**: MapLibre GIS integration layer in frontend, Celery COG generation options.
- **Resolution Deadline**: **Phase 7 (Farmer Portal Implementation)**.

---

### Decision 3: Production Cloud Hosting Topology
- **Current Status**: PROPOSED (Azure Container Apps + Dedicated WebODM GPU/Compute VM).
- **Options Under Consideration**:
  1. *Option A (Azure Container Apps + WebODM VM Scale Set)*: Serverless container hosting for Next.js, FastAPI, and Celery workers with KEDA autoscaling; high-CPU VM for NodeODM. Cost-effective, scales to zero when idle.
  2. *Option B (Azure Kubernetes Service - AKS)*: Unified enterprise Kubernetes cluster managing all pods including NodeODM. Maximum operational flexibility, but higher DevOps management overhead.
  3. *Option C (Hybrid Cloud / Self-Hosted Docker)*: Next.js on Vercel; FastAPI, PostgreSQL, and WebODM hosted on an on-premises dedicated Linux server.
- **Why It Matters**: Influences deployment scripts, network configuration, and monthly operational cloud infrastructure expenses.
- **Dependencies**: Production CI/CD pipelines, Terraform / Bicep templates.
- **Resolution Deadline**: **Phase 9 (Deployment & Production Setup)**.

---

### Decision 4: Default Colormap for Vegetation Indices (Accessibility)
- **Current Status**: OPEN FOR USER CONFIRMATION.
- **Options Under Consideration**:
  1. *Option A (`RdYlGn` - Red-Yellow-Green)*: The traditional agronomic standard intuitive to most farmers (Green = healthy, Red = stressed). However, problematic for individuals with Red-Green color vision deficiency (deuteranopia).
  2. *Option B (`Viridis` / `Plasma` - Perceptually Uniform)*: Mathematically uniform, accessible to colorblind users, prints cleanly in grayscale. Less traditional for non-technical agricultural audiences.
- **Why It Matters**: Determines the default visual ramp displayed on the interactive map (Page 4) and in compiled PDF audit reports (Page 5). Both colormaps are supported by the raster engine.
- **Dependencies**: Frontend legend controls, ReportLab PDF color mapping.
- **Resolution Deadline**: **Phase 6 (Spectral Algorithm Implementation)**.

---

### Decision 5: Mobile GIS Layer Switcher UI Pattern
- **Current Status**: OPEN FOR USER CONFIRMATION.
- **Options Under Consideration**:
  1. *Option A (Slide-Up Bottom Sheet)*: Drag-handle drawer rising from the bottom of the phone screen, keeping the upper map visible.
  2. *Option B (Full-Screen Modal)*: Standard overlay dialog completely covering the map during layer selection.
- **Why It Matters**: Dictates touch ergonomics and map visibility on mobile viewports ($< 768\text{px}$).
- **Dependencies**: `frontend/components/gis/LayerControl.tsx`.
- **Resolution Deadline**: **Phase 7 (Farmer Portal Implementation)**.
