# System Security Review & Threat Assessment

**Document:** Application Security & Vulnerability Assessment  
**Phase:** Phase 10  
**Status:** Completed  
**Date:** October 2026  
**Security Classification:** Confidential  

---

## 1. Executive Summary

A comprehensive application security review was conducted across the frontend (Next.js), backend API (FastAPI), database (PostgreSQL/PostGIS), worker pipeline (Celery/Redis), and file storage integration (Azure Blob Storage).

The review confirms that the critical security objectives established in Phase 9—specifically multi-tenant data isolation, anti-IDOR controls, password hashing, and token signature verification—are rigorously enforced without regression.

---

## 2. Threat Vector Assessment & Controls Matrix

| Threat Category | Potential Risk | Implemented Control | Status |
| :--- | :--- | :--- | :---: |
| **Broken Object Level Auth (IDOR)** | Farmer querying competitor's field, raster, or report | Relational traversal in `deps.py` (`resource -> survey -> field -> farm.owner_id == user.id`). | **PROTECTED** |
| **Resource Enumeration** | Competitor checking if another farm ID exists | Privacy-preserving `HTTP 404 Not Found` returned on all unauthorized queries. | **PROTECTED** |
| **Credential Stuffing / Brute Force**| Automated password guessing attacks | In-memory sliding window rate limiter (20 requests / 60 seconds per IP) on `/auth/login`. | **PROTECTED** |
| **Weak Password Storage** | Database compromise exposing passwords | Bcrypt password hashing with 12 salt rounds; constant-time verification. | **PROTECTED** |
| **Token Tampering** | Forging administrative roles in JWT payload | HS256 signature verification using server-side `SECRET_KEY`; registered claims validated. | **PROTECTED** |
| **Cross-Site Scripting (XSS)** | Stealing session tokens from browser memory | Session tokens stored in `HttpOnly` cookies inaccessible to JavaScript `document.cookie`. | **PROTECTED** |
| **Cross-Site Request Forgery (CSRF)**| Malicious site triggering actions on behalf of farmer | `SameSite=Lax` cookie policy; programmatic API calls require `Authorization: Bearer` header. | **PROTECTED** |
| **Open Redirect Vulnerability** | Phishing via `/login?returnUrl=...` parameter | Validation strictly enforces leading single `/` and blocks `//` or protocol schemas. | **PROTECTED** |
| **SQL Injection (SQLi)** | Arbitrary SQL execution via input parameters | 100% parameterized queries via SQLAlchemy 2.0 ORM; zero raw string interpolation. | **PROTECTED** |
| **Path Traversal (LFI)** | Downloading system files via `/files/.../download` | Storage adapter uses `_resolve_safe_path` with strict base directory resolution and check. | **PROTECTED** |
| **Public Storage Exposure** | Leaking raw drone photos or private GeoTIFFs | Azure containers set to Private; server returns short-lived, narrowly-scoped SAS URLs (15m). | **PROTECTED** |
| **Log Credential Leaks** | Passwords or tokens appearing in server logs | Structured logger redacts authorization headers, passwords, and sensitive parameters. | **PROTECTED** |

---

## 3. Storage & Map Tile Security Audit

### Azure Blob Storage Integration
- All containers (`raw-surveys`, `orthomosaics`, `vegetation-indices`, `reports`) are strictly configured with public access disabled (`Private`).
- When a client requests a file download, the backend validates tenant ownership and uses the official `azure-storage-blob` Python SDK to generate a temporary Shared Access Signature (SAS) URL with `read=True` and a 15-minute expiration timestamp.
- No master storage account keys or SAS tokens with write/delete permissions are ever shared with the browser.

### MapLibre Tile Delivery
- MapLibre GL JS renders raster overlays by requesting XYZ slippy tiles (`/api/v1/maps/tiles/{id}/{z}/{x}/{y}.png`).
- Tiles are protected by dual authentication:
  1. `access_token` session cookie (transmitted automatically by browser image loaders).
  2. Fallback query parameter `?token=<jwt_access_token>`.
- The tile endpoint queries `verify_map_product_access` to confirm that the requesting user owns the underlying agricultural survey before rendering the tile.

---

## 4. Production Hardening Checklist for Deployment

Before deploying to a public production URL, the following standard operational configurations must be applied:

1. **Production Secret Key:** Generate a cryptographically random 64-character string for `SECRET_KEY` (e.g., using `openssl rand -hex 32`).
2. **HTTPS & Secure Cookies:** Set `COOKIE_SECURE=true` in `.env` to enforce HTTPS-only transmission.
3. **CORS Restriction:** Replace localhost development origins in `CORS_ORIGINS` with the exact production domain (e.g. `["https://app.agridrone.com"]`).
4. **Redis Rate Limiting (Multi-Pod):** For horizontally scaled Kubernetes deployments, configure Redis-backed rate limiting to coordinate request counters across multiple API pods.
