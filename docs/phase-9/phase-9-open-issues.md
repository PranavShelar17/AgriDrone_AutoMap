# Phase 9 Known Limitations & Open Issues

**Document:** Risk Assessment & Technical Backlog — Phase 9  
**Status:** Documented  
**Date:** October 2026  

---

## 1. Architectural Observations & Notes

### 1.1 In-Memory Rate Limiter on Authentication
- **Current Behavior:** The brute-force protection rate limiter on `/api/v1/auth/login` uses an in-memory dictionary tracking IP timestamps over a 60-second window.
- **Suitability:** Highly reliable and performant for single-node deployments, local Docker Compose setups, and edge drone stations.
- **Phase 10 Recommendation:** If deploying to a horizontally auto-scaled multi-container Kubernetes cluster, transition the rate-limiter backend to the existing Redis instance (`REDIS_URL`) using Redis sorted sets (`ZREMRANGEBYSCORE`).

### 1.2 Token Invalidation Strategy (Stateless vs Blacklist)
- **Current Behavior:** JWTs are cryptographically signed and valid for 480 minutes (8 hours). Logout clears the browser cookie and local storage. When an account is disabled via `POST /api/v1/auth/status`, the backend immediately denies access on the very next request because `get_current_user` queries `db.query(User).filter(User.id == user_id, User.is_active == True).first()`.
- **Phase 10 Recommendation:** If immediate invalidation of non-expired tokens is required for active, enabled users prior to natural expiry, implement a Redis-backed JWT revocation blocklist.

### 1.3 Administrative User Interface
- **Current Behavior:** Farmer account creation and farm assignment endpoints (`POST /auth/register-farmer`, `POST /auth/assign-farm`) are fully functional and secured with `get_current_active_admin`. 
- **Preservation of Core Pages:** Per Section 1 of the Master Prompt ("The platform has exactly five main functional areas... Keep these five functional areas intact"), no additional 6th major page was created. Account onboarding is executed programmatically or via backend management scripts.

### 1.4 Self-Service Password Reset & Email Verification
- **Current Behavior:** Consistent with Section 5 ("Do not invent an unrestricted public signup process... Implement them only when appropriate to the approved requirements"), public registration is intentionally disabled.
- **Phase 10 Recommendation:** When cloud SMTP or transactional email providers (SendGrid / Azure Communication Services) are provisioned in Phase 10, automated invitation and password reset email links can be enabled.
