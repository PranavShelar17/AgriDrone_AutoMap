# Architecture Decision Record: Authentication & Authorization Strategy

**Document:** ADR-009-AUTH  
**Status:** Approved & Implemented  
**Date:** October 2026  
**Context:** AgriDrone AutoMap Phase 9  

---

## 1. Context & Problem Statement

AgriDrone AutoMap processes sensitive agricultural intelligence, including high-resolution drone orthomosaics, vegetation index rasters, PostGIS field boundaries, and farm financial diagnostics. 

During Phase 3 architecture design ([docs/phase-3/phase-3-open-decisions.md](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-3/phase-3-open-decisions.md)), Open Decision #3 identified the need for a production-grade authentication and authorization mechanism that isolates farmer tenants without introducing recurring cloud costs or complex external dependencies.

Phase 9 requires selecting and implementing an approved authentication and authorization strategy that integrates seamlessly with the existing Next.js, FastAPI, and PostgreSQL architecture.

---

## 2. Evaluated Options

### Option A: Self-Hosted First-Party Authentication (Bcrypt + PyJWT + FastAPI Dependencies)
- **Mechanism:** Direct authentication via FastAPI `/api/v1/auth/login`. Password verification using Bcrypt (`bcrypt.hashpw` with 12 salt rounds). Cryptographically signed JSON Web Tokens (`PyJWT`, `HS256`, 8-hour expiration). Delivered via dual channels: `Authorization: Bearer <token>` header and secure `HttpOnly`, `SameSite=Lax` session cookies.
- **Pros:**
  - Zero ongoing software or cloud identity costs ($0/month).
  - Completely self-contained; zero vendor lock-in.
  - Fully compatible with local development, automated Docker Compose clusters, and offline/air-gapped edge deployments on agricultural sites.
  - Leverages the existing PostgreSQL `users` table, SQLAlchemy ORM, and `audit_logs` table.
  - Complete control over rate limiting, token lifecycles, and audit logging.
- **Cons:**
  - Password reset and email confirmation infrastructure must be maintained if needed in future releases.
  - MFA requires custom implementation in Phase 10 if required.

### Option B: Managed External Cloud IdP (Azure AD B2C, Auth0, AWS Cognito)
- **Mechanism:** Delegate authentication to a SaaS identity provider using OpenID Connect (OIDC) and OAuth 2.0.
- **Pros:**
  - Built-in multi-factor authentication (MFA) and social identity providers.
  - Hosted user management dashboards.
- **Cons:**
  - Recurring monthly costs per active user (MAU).
  - High vendor lock-in and dependency on cloud network availability (cannot operate on remote farms without Internet connectivity).
  - Requires creating and configuring external cloud accounts and managing client secrets across environments.

### Option C: Self-Hosted Identity Server (Keycloak / Authentik)
- **Mechanism:** Run an independent identity server container alongside the platform.
- **Pros:**
  - OIDC standard compliance with self-hosted control.
- **Cons:**
  - Excessive infrastructure overhead (Keycloak requires substantial JVM memory footprint of 1.5GB+ RAM).
  - Over-complicates local development and container orchestration for a targeted 5-page platform.

---

## 3. Decision & Trade-off Matrix

| Metric | Option A: Self-Hosted Bcrypt + PyJWT | Option B: Managed Cloud IdP | Option C: Keycloak / Authentik |
| :--- | :--- | :--- | :--- |
| **Licensing / Cloud Cost** | **$0.00** | $0.02 - $0.15 / MAU | $0.00 |
| **Operational Simplicity** | **High** (Embedded in FastAPI) | Medium (Cloud Console) | Low (Heavy secondary container) |
| **External Dependencies** | **None** | High (Internet required) | Medium (Java/Postgres) |
| **Air-Gapped Deployment** | **Full Support** | Not Supported | Supported |
| **Test Automation** | **Fast & Isolated (<10s)** | Complex (Mocking required)| Slow container startup |
| **Stack Alignment** | **100% Native Python/FastAPI**| External redirects | External redirects |

---

## 4. Final Decision

**Approved Choice: Option A (Self-Hosted First-Party Bcrypt + PyJWT + FastAPI Ownership Guards).**

### Key Implementation Principles:
1. **Password Hashing:** Bcrypt with 12 rounds of salting and constant-time comparison to prevent timing attacks.
2. **Token Security:** HS256 algorithm with minimum 32-character server-side `SECRET_KEY`, 480-minute (8-hour) expiration, and registered claims (`sub`, `role`, `email`, `iat`, `exp`).
3. **Dual Delivery:**
   - Single Page App (SPA) API calls: `Authorization: Bearer <token>` attached automatically by the frontend HTTP client.
   - MapLibre GL Tile Requests: Dual support via `access_token` session cookie and `?token=` query parameter fallback.
4. **Anti-Brute Force:** In-memory rolling rate limiter on `/auth/login` (20 attempts per minute per IP address).
5. **Privacy-Preserving 404s:** Unauthorized resource queries return HTTP 404 with generic messages, preventing enumeration of competitor farm assets.
