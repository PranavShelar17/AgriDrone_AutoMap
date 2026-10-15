# Operational Incident Response Runbook

**Document:** Incident Management & Recovery Procedures  
**Phase:** Phase 10  
**Status:** Approved  
**Date:** October 2026  

---

## 1. Incident Severity Definitions

- **Severity 1 (Critical Outage):** Complete platform unavailability, database connectivity failure, or security breach. Response SLA: < 15 minutes.
- **Severity 2 (Degraded Performance):** Core workflows impaired (e.g., photogrammetry jobs stuck, map tile rendering slow), but portal accessible. Response SLA: < 1 hour.
- **Severity 3 (Minor Issue):** Cosmetic UI defect or non-critical background task delay with workaround available. Response SLA: < 8 hours.

---

## 2. Standard Incident Runbooks

### Runbook 1: Database Connection Failure or PostGIS Lockup
**Symptoms:** `/api/v1/health/readiness` returns `503 Service Unavailable`, logs report `OperationalError: could not connect to server`.

1. **Verify Database Container Status:**
   ```bash
   docker ps -f name=agridrone_prod_db
   ```
2. **Inspect Database Logs for OOM or Storage Limits:**
   ```bash
   docker logs --tail 100 agridrone_prod_db
   ```
3. **Check Active Queries & Locks:**
   ```bash
   docker exec -it agridrone_prod_db psql -U agridrone_user -d agridrone_db -c "SELECT pid, now() - query_start as duration, query, state FROM pg_stat_activity WHERE state != 'idle';"
   ```
4. **Terminate Blocking Locks (if necessary):**
   ```sql
   SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE duration > interval '5 minutes' AND state != 'idle';
   ```
5. **Restart Service:**
   ```bash
   docker restart agridrone_prod_db
   ```

---

### Runbook 2: Celery Worker Queue Starvation / Stalled Jobs
**Symptoms:** Photogrammetry or algorithm jobs remain in `QUEUED` state indefinitely.

1. **Check Active Worker Nodes:**
   ```bash
   docker exec -it agridrone_prod_worker celery -A app.core.celery_app.celery_app status
   ```
2. **Inspect Queue Depth in Redis:**
   ```bash
   docker exec -it agridrone_prod_redis redis-cli llen photogrammetry
   docker exec -it agridrone_prod_redis redis-cli llen raster_analytics
   ```
3. **Check Worker Resource Saturation:**
   ```bash
   docker stats agridrone_prod_worker
   ```
4. **Remediation:** If worker crashed due to memory exhaustion during high-res raster math, scale worker instances:
   ```bash
   docker compose -f docker-compose.prod.yml up -d --scale worker=2
   ```

---

### Runbook 3: NodeODM Photogrammetry Node Failure
**Symptoms:** Photogrammetry tasks fail immediately or report `502 Bad Gateway` when contacting NodeODM.

1. **Check NodeODM Container Liveness:**
   ```bash
   curl http://localhost:3001/info
   ```
2. **Review NodeODM Processing Logs:**
   ```bash
   docker logs --tail 200 agridrone_nodeodm
   ```
3. **Common Cause — Out of Memory (OOM):** NodeODM requires at least 4GB to 8GB of RAM for 100+ photo surveys. Check host memory allocation.
4. **Restart NodeODM:**
   ```bash
   docker restart agridrone_nodeodm
   ```

---

### Runbook 4: Suspected Brute-Force Authentication Attack
**Symptoms:** High frequency of failed login alerts, CPU spike on auth route.

1. **Query Security Audit Logs for Offending IP Addresses:**
   ```sql
   SELECT ip_address, count(*) as failure_count
   FROM audit_logs
   WHERE action = 'LOGIN_FAILED' AND created_at > now() - interval '1 hour'
   GROUP BY ip_address
   ORDER BY failure_count DESC
   LIMIT 10;
   ```
2. **Immediate Firewall Block (NGINX / Cloudflare / UFW):**
   ```bash
   sudo ufw deny from <offending_ip_address> to any port 80,443
   ```
3. **Verify Legitimate Users:** Ensure legitimate farmer accounts are not locked out; reset password if targeted account was compromised.

---

### Runbook 5: Local Disk Space Saturation
**Symptoms:** Ingestion photo uploads fail with `500 Internal Server Error`, Uvicorn logs report `No space left on device`.

1. **Inspect Disk Consumption:**
   ```bash
   df -h /
   ```
2. **Purge Dangling Docker Build Cache & Scratch Files:**
   ```bash
   docker system prune -f
   # Clean temporary raster processing directories older than 24 hours
   find /tmp -name "raster_batch_*" -mtime +1 -exec rm -rf {} +
   ```
3. **Verify Azure Upload Completion:** Ensure local storage is configured to forward completed rasters to Azure Blob Storage rather than accumulating indefinitely.
