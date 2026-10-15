import os
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

# WebODM Numeric Status Codes mapping
WEBODM_STATUS_MAP = {
    10: "QUEUED",
    20: "RUNNING",
    30: "FAILED",
    40: "COMPLETED",
    50: "CANCELLED",
}

# Supported WebODM processing options whitelist
VALID_WEBODM_OPTIONS = {
    "dsm": bool,
    "dtm": bool,
    "auto-boundary": bool,
    "radiometric-calibration": (str, bool),
    "orthophoto-resolution": (int, float),
    "feature-quality": str,
    "pc-quality": str,
    "mesh-quality": str,
    "max-concurrency": int,
    "min-num-features": int,
    "matcher-neighbors": int,
    "mesh-size": int,
    "fast-orthophoto": bool,
}

FEATURE_QUALITY_CHOICES = {"ultra", "high", "medium", "low", "lowest"}
PC_QUALITY_CHOICES = {"ultra", "high", "medium", "low", "lowest"}


class WebODMError(Exception):
    """Base exception for WebODM integration errors."""
    pass


class WebODMConnectionError(WebODMError):
    """Raised when WebODM service is unreachable or offline."""
    pass


class WebODMAuthenticationError(WebODMError):
    """Raised when authentication credentials fail."""
    pass


class WebODMService:
    """Production service client for WebODM and NodeODM photogrammetry clusters."""

    def __init__(
        self,
        api_url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        self.api_url = (api_url or settings.WEBODM_API_URL).rstrip("/")
        self.username = username or settings.WEBODM_USERNAME
        self.password = password or settings.WEBODM_PASSWORD
        self.timeout = timeout or settings.WEBODM_TIMEOUT_SECONDS
        self._auth_token: Optional[str] = settings.WEBODM_TOKEN
        self._default_project_id: Optional[int] = settings.WEBODM_PROJECT_ID

    def _get_headers(self) -> Dict[str, str]:
        headers = {"Accept": "application/json"}
        if self._auth_token:
            headers["Authorization"] = f"JWT {self._auth_token}"
        return headers

    def authenticate(self) -> str:
        """Authenticate with WebODM and obtain JWT session token."""
        if self._auth_token:
            return self._auth_token

        auth_url = f"{self.api_url}/api/token-auth/"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(
                    auth_url,
                    json={"username": self.username, "password": self.password},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    self._auth_token = data.get("token")
                    logger.info("Successfully authenticated with WebODM at %s", self.api_url)
                    return self._auth_token
                elif resp.status_code in (400, 401, 403):
                    raise WebODMAuthenticationError(
                        f"WebODM authentication failed (HTTP {resp.status_code}): {resp.text}"
                    )
                else:
                    raise WebODMConnectionError(
                        f"Unexpected response from WebODM token auth (HTTP {resp.status_code}): {resp.text}"
                    )
        except httpx.RequestError as e:
            raise WebODMConnectionError(f"Cannot reach WebODM at {self.api_url}: {str(e)}")

    def check_cluster_health(self) -> Dict[str, Any]:
        """Probes WebODM or NodeODM instance to verify connectivity and capacity."""
        result: Dict[str, Any] = {
            "cluster_status": "OFFLINE",
            "is_connected": False,
            "api_url": self.api_url,
            "engine": "WebODM",
            "active_nodes": 0,
            "total_nodes": 0,
            "available_ram_gb": None,
            "details": "Service unreachable",
            "error_message": None,
            "timestamp": datetime.utcnow().isoformat(),
        }

        try:
            with httpx.Client(timeout=min(self.timeout, 5)) as client:
                # 1. First check if it is a NodeODM direct node
                try:
                    node_resp = client.get(f"{self.api_url}/info")
                    if node_resp.status_code == 200:
                        node_data = node_resp.json()
                        result.update({
                            "cluster_status": "ONLINE",
                            "is_connected": True,
                            "engine": "NodeODM",
                            "active_nodes": 1,
                            "total_nodes": 1,
                            "available_ram_gb": round(node_data.get("availableMemory", 0) / (1024**3), 2)
                            if node_data.get("availableMemory")
                            else None,
                            "details": f"NodeODM {node_data.get('version', '')} online (Queue: {node_data.get('taskQueueCount', 0)})",
                        })
                        return result
                except Exception:
                    pass

                # 2. Check full WebODM endpoint
                auth_probe = client.get(f"{self.api_url}/api/projects/", headers=self._get_headers())
                if auth_probe.status_code in (200, 401, 403):
                    # Service is running. Check cluster nodes if authenticated
                    result["is_connected"] = True
                    result["cluster_status"] = "ONLINE"
                    result["details"] = "WebODM cluster is online and responding."

                    # Attempt node listing if token available or try authenticating
                    try:
                        self.authenticate()
                        cluster_resp = client.get(f"{self.api_url}/api/cluster/nodes/", headers=self._get_headers())
                        if cluster_resp.status_code == 200:
                            nodes = cluster_resp.json()
                            active = [n for n in nodes if n.get("online", False)]
                            result["total_nodes"] = len(nodes)
                            result["active_nodes"] = len(active)
                            result["details"] = f"WebODM cluster online ({len(active)}/{len(nodes)} processing nodes active)"
                    except Exception as auth_err:
                        result["details"] = f"WebODM responding (Authentication pending or credentials unverified: {str(auth_err)})"
                    return result
                else:
                    result["error_message"] = f"WebODM returned unexpected HTTP status: {auth_probe.status_code}"
                    return result

        except httpx.ConnectError:
            result["error_message"] = f"Connection refused at {self.api_url}. Is WebODM / Docker running?"
            return result
        except httpx.TimeoutException:
            result["error_message"] = f"Connection timed out after {min(self.timeout, 5)}s connecting to {self.api_url}."
            return result
        except Exception as e:
            result["error_message"] = f"WebODM probe failed: {str(e)}"
            return result

    def get_or_create_project(self, project_name: str = "AgriDrone AutoMap") -> int:
        """Finds or creates the designated WebODM project container."""
        if self._default_project_id:
            return self._default_project_id

        self.authenticate()
        headers = self._get_headers()

        with httpx.Client(timeout=self.timeout) as client:
            # List existing projects
            resp = client.get(f"{self.api_url}/api/projects/", headers=headers)
            if resp.status_code == 200:
                projects = resp.json()
                results = projects.get("results", projects) if isinstance(projects, dict) else projects
                for p in results:
                    if p.get("name") == project_name:
                        self._default_project_id = int(p["id"])
                        return self._default_project_id

            # Create project if not found
            create_resp = client.post(
                f"{self.api_url}/api/projects/",
                headers=headers,
                json={"name": project_name, "description": "Automated drone photogrammetry project"},
            )
            if create_resp.status_code in (200, 201):
                p_data = create_resp.json()
                self._default_project_id = int(p_data["id"])
                logger.info("Created WebODM project '%s' with ID %d", project_name, self._default_project_id)
                return self._default_project_id
            else:
                raise WebODMError(f"Failed to create WebODM project (HTTP {create_resp.status_code}): {create_resp.text}")

    def build_options_payload(
        self,
        resolution_preset: str = "HIGH_RES",
        custom_resolution_cm: Optional[float] = None,
        generate_dsm: bool = True,
        generate_dtm: bool = True,
        radiometric_calibration: bool = False,
        feature_quality: str = "high",
        pc_quality: str = "medium",
    ) -> List[Dict[str, Any]]:
        """Constructs and validates the WebODM photogrammetry options list."""
        options: List[Dict[str, Any]] = [
            {"name": "auto-boundary", "value": True},
            {"name": "dsm", "value": bool(generate_dsm)},
            {"name": "dtm", "value": bool(generate_dtm)},
        ]

        # Resolution GSD
        if custom_resolution_cm and custom_resolution_cm > 0:
            options.append({"name": "orthophoto-resolution", "value": float(custom_resolution_cm)})
        elif resolution_preset.upper() == "FAST":
            options.append({"name": "orthophoto-resolution", "value": 5.0})
            options.append({"name": "fast-orthophoto", "value": True})
        else:
            # Default HIGH_RES (2.5 cm/px)
            options.append({"name": "orthophoto-resolution", "value": 2.5})

        # Feature Quality
        fq = feature_quality.lower() if feature_quality.lower() in FEATURE_QUALITY_CHOICES else "high"
        options.append({"name": "feature-quality", "value": fq})

        # Point Cloud Quality
        pq = pc_quality.lower() if pc_quality.lower() in PC_QUALITY_CHOICES else "medium"
        options.append({"name": "pc-quality", "value": pq})

        # Radiometric calibration
        if radiometric_calibration:
            options.append({"name": "radiometric-calibration", "value": "camera+sun"})
        else:
            options.append({"name": "radiometric-calibration", "value": "none"})

        return options

    def create_task(
        self,
        task_name: str,
        image_files: List[Tuple[str, bytes]],
        options: List[Dict[str, Any]],
        project_id: Optional[int] = None,
    ) -> str:
        """Submits a photogrammetry task with image binaries to WebODM."""
        if not image_files:
            raise WebODMError("Cannot create photogrammetry task without source images.")

        p_id = project_id or self.get_or_create_project()
        self.authenticate()
        headers = self._get_headers()
        # Remove Content-Type so httpx computes multipart boundary
        headers.pop("Content-Type", None)

        task_url = f"{self.api_url}/api/projects/{p_id}/tasks/"

        # Format options as JSON string
        data_fields = {
            "name": task_name,
            "options": json.dumps(options),
        }

        # Multi-file payload
        multipart_files = [
            ("images", (filename, data, "image/jpeg" if filename.lower().endswith((".jpg", ".jpeg")) else "application/octet-stream"))
            for filename, data in image_files
        ]

        try:
            with httpx.Client(timeout=httpx.Timeout(120.0, connect=self.timeout)) as client:
                resp = client.post(
                    task_url,
                    headers=headers,
                    data=data_fields,
                    files=multipart_files,
                )
                if resp.status_code in (200, 201):
                    res_json = resp.json()
                    task_uuid = res_json.get("id") or res_json.get("uuid")
                    if not task_uuid:
                        raise WebODMError("WebODM task created but no task UUID was returned.")
                    logger.info("Successfully created WebODM task '%s' (UUID: %s)", task_name, task_uuid)
                    return str(task_uuid)
                else:
                    raise WebODMError(
                        f"Failed to submit task to WebODM (HTTP {resp.status_code}): {resp.text}"
                    )
        except httpx.RequestError as e:
            raise WebODMConnectionError(f"Network error while dispatching task to WebODM: {str(e)}")

    def get_task_status(self, task_uuid: str, project_id: Optional[int] = None) -> Dict[str, Any]:
        """Polls current task status, progress percentage, stage, and execution times."""
        p_id = project_id or self.get_or_create_project()
        self.authenticate()
        headers = self._get_headers()

        status_url = f"{self.api_url}/api/projects/{p_id}/tasks/{task_uuid}/"

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(status_url, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    status_code = data.get("status", 10)
                    status_str = WEBODM_STATUS_MAP.get(status_code, "RUNNING" if status_code == 20 else "QUEUED")

                    # Stage & Progress
                    progress = int(data.get("progress", 0) or 0)
                    last_error = data.get("last_error")

                    return {
                        "webodm_task_uuid": task_uuid,
                        "status": status_str,
                        "status_code": status_code,
                        "progress_percent": min(max(progress, 0), 100),
                        "current_stage": data.get("status_text") or f"Stage {status_str}",
                        "processing_time_ms": data.get("processing_time"),
                        "error_message": last_error,
                        "available_assets": data.get("available_assets", []),
                    }
                elif resp.status_code == 404:
                    raise WebODMError(f"Task UUID '{task_uuid}' not found on WebODM project {p_id}.")
                else:
                    raise WebODMError(
                        f"Failed to fetch WebODM task status (HTTP {resp.status_code}): {resp.text}"
                    )
        except httpx.RequestError as e:
            raise WebODMConnectionError(f"Failed to query WebODM task status: {str(e)}")

    def get_task_logs(
        self, task_uuid: str, project_id: Optional[int] = None, line_offset: int = 0
    ) -> List[str]:
        """Retrieves execution console log lines from WebODM."""
        p_id = project_id or self.get_or_create_project()
        self.authenticate()
        headers = self._get_headers()

        logs_url = f"{self.api_url}/api/projects/{p_id}/tasks/{task_uuid}/output/"

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(logs_url, headers=headers)
                if resp.status_code == 200:
                    output_data = resp.json()
                    lines: List[str] = []
                    if isinstance(output_data, list):
                        lines = [str(line).rstrip() for line in output_data]
                    elif isinstance(output_data, str):
                        lines = [l.rstrip() for l in output_data.split("\n") if l.strip()]
                    elif isinstance(output_data, dict):
                        raw = output_data.get("output", [])
                        if isinstance(raw, list):
                            lines = [str(l).rstrip() for l in raw]
                        elif isinstance(raw, str):
                            lines = [l.rstrip() for l in raw.split("\n") if l.strip()]

                    if line_offset > 0:
                        return lines[line_offset:]
                    return lines
                elif resp.status_code == 404:
                    return [f"Task {task_uuid} has not generated console output yet."]
                else:
                    return [f"Unable to read logs (HTTP {resp.status_code})"]
        except Exception as e:
            logger.warning("Error fetching task logs from WebODM: %s", str(e))
            return [f"Connection error retrieving WebODM logs: {str(e)}"]

    def cancel_task(self, task_uuid: str, project_id: Optional[int] = None) -> bool:
        """Sends cancellation request for an active WebODM task."""
        p_id = project_id or self.get_or_create_project()
        self.authenticate()
        headers = self._get_headers()

        cancel_url = f"{self.api_url}/api/projects/{p_id}/tasks/{task_uuid}/cancel/"

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(cancel_url, headers=headers)
                if resp.status_code in (200, 202, 204):
                    logger.info("Cancelled WebODM task %s", task_uuid)
                    return True
                else:
                    logger.warning("WebODM cancel response HTTP %d: %s", resp.status_code, resp.text)
                    return False
        except Exception as e:
            raise WebODMError(f"Failed to cancel WebODM task: {str(e)}")

    def download_artifact(
        self,
        task_uuid: str,
        asset_name: str,
        project_id: Optional[int] = None,
    ) -> bytes:
        """Downloads a specific photogrammetry output artifact (e.g. 'orthophoto.tif', 'dsm.tif')."""
        p_id = project_id or self.get_or_create_project()
        self.authenticate()
        headers = self._get_headers()

        download_url = f"{self.api_url}/api/projects/{p_id}/tasks/{task_uuid}/download/{asset_name}"

        try:
            with httpx.Client(timeout=httpx.Timeout(180.0, connect=self.timeout)) as client:
                resp = client.get(download_url, headers=headers)
                if resp.status_code == 200:
                    return resp.content
                elif resp.status_code == 404:
                    raise FileNotFoundError(f"Artifact '{asset_name}' not found for WebODM task {task_uuid}.")
                else:
                    raise WebODMError(
                        f"Failed to download artifact '{asset_name}' (HTTP {resp.status_code}): {resp.text}"
                    )
        except httpx.RequestError as e:
            raise WebODMConnectionError(f"Failed to download artifact from WebODM: {str(e)}")


_webodm_instance: Optional[WebODMService] = None


def get_webodm_service() -> WebODMService:
    """Factory to retrieve configured WebODM service singleton."""
    global _webodm_instance
    if _webodm_instance is None:
        _webodm_instance = WebODMService()
    return _webodm_instance
