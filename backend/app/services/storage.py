import os
import re
import hashlib
import logging
from abc import ABC, abstractmethod
from typing import BinaryIO, Dict, Any, Optional
from datetime import datetime, timedelta

from app.core.config import settings

logger = logging.getLogger(__name__)


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent directory traversal and remove unsafe characters."""
    # Strip any directory path components
    base_name = os.path.basename(filename)
    # Replace any non-alphanumeric, dash, underscore, dot with underscore
    clean_name = re.sub(r"[^a-zA-Z0-9._-]", "_", base_name)
    # Ensure it's not empty or just dots
    if not clean_name or clean_name.strip(".") == "":
        clean_name = f"unnamed_file_{int(datetime.utcnow().timestamp())}.dat"
    return clean_name


def build_blob_path(prefix: str, filename: str) -> str:
    """Build controlled object path: {prefix}/{safe_filename}."""
    safe_name = sanitize_filename(filename)
    clean_prefix = re.sub(r"[^a-zA-Z0-9_-]", "_", str(prefix).strip("/"))
    return f"{clean_prefix}/{safe_name}"


class BaseStorageService(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of storage provider ('azure_blob' or 'local_dev')."""
        pass

    @abstractmethod
    def upload_file(
        self,
        file_obj: BinaryIO,
        container: str,
        blob_path: str,
        content_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Upload file object and return metadata dict with hashes and URI."""
        pass

    @abstractmethod
    def download_file(self, container: str, blob_path: str) -> bytes:
        """Download file content into memory."""
        pass

    @abstractmethod
    def delete_file(self, container: str, blob_path: str) -> bool:
        """Delete file from storage."""
        pass

    @abstractmethod
    def file_exists(self, container: str, blob_path: str) -> bool:
        """Check if file exists in storage."""
        pass

    @abstractmethod
    def get_access_url(
        self, container: str, blob_path: str, expiry_minutes: int = 60
    ) -> str:
        """Generate a secure, short-lived download/read URL."""
        pass


class AzureBlobStorageService(BaseStorageService):
    """Production Azure Blob Storage client using official azure-storage-blob SDK."""

    def __init__(self, connection_string: str, account_name: str):
        from azure.storage.blob import BlobServiceClient

        self.account_name = account_name
        self.connection_string = connection_string
        self.client = BlobServiceClient.from_connection_string(connection_string)
        logger.info("Initialized AzureBlobStorageService for account: %s", account_name)

    @property
    def provider_name(self) -> str:
        return "azure_blob"

    def _get_container_client(self, container: str):
        container_client = self.client.get_container_client(container)
        if not container_client.exists():
            container_client.create_container()
        return container_client

    def upload_file(
        self,
        file_obj: BinaryIO,
        container: str,
        blob_path: str,
        content_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        from azure.storage.blob import ContentSettings

        container_client = self._get_container_client(container)
        blob_client = container_client.get_blob_client(blob_path)

        md5 = hashlib.md5()
        sha256 = hashlib.sha256()
        total_bytes = 0

        # Read stream and compute hashes while buffering
        chunks = []
        while True:
            chunk = file_obj.read(1024 * 1024)  # 1MB chunks
            if not chunk:
                break
            md5.update(chunk)
            sha256.update(chunk)
            total_bytes += len(chunk)
            chunks.append(chunk)

        data = b"".join(chunks)

        cnt_settings = ContentSettings(content_type=content_type) if content_type else None
        blob_client.upload_blob(data, overwrite=True, content_settings=cnt_settings)

        blob_uri = f"https://{self.account_name}.blob.core.windows.net/{container}/{blob_path}"
        return {
            "provider": self.provider_name,
            "container": container,
            "blob_path": blob_path,
            "blob_uri": blob_uri,
            "file_size_bytes": total_bytes,
            "md5_checksum": md5.hexdigest(),
            "sha256_checksum": sha256.hexdigest(),
        }

    def download_file(self, container: str, blob_path: str) -> bytes:
        container_client = self.client.get_container_client(container)
        blob_client = container_client.get_blob_client(blob_path)
        return blob_client.download_blob().readall()

    def delete_file(self, container: str, blob_path: str) -> bool:
        container_client = self.client.get_container_client(container)
        blob_client = container_client.get_blob_client(blob_path)
        if blob_client.exists():
            blob_client.delete_blob()
            return True
        return False

    def file_exists(self, container: str, blob_path: str) -> bool:
        container_client = self.client.get_container_client(container)
        blob_client = container_client.get_blob_client(blob_path)
        return blob_client.exists()

    def get_access_url(
        self, container: str, blob_path: str, expiry_minutes: int = 60
    ) -> str:
        from azure.storage.blob import generate_blob_sas, BlobSasPermissions

        # Extract account key if connection string contains AccountKey
        key_match = re.search(r"AccountKey=([^;]+)", self.connection_string)
        if key_match:
            account_key = key_match.group(1)
            sas_token = generate_blob_sas(
                account_name=self.account_name,
                container_name=container,
                blob_name=blob_path,
                account_key=account_key,
                permission=BlobSasPermissions(read=True),
                expiry=datetime.utcnow() + timedelta(minutes=expiry_minutes),
            )
            return f"https://{self.account_name}.blob.core.windows.net/{container}/{blob_path}?{sas_token}"
        # Fallback to direct URI if SAS cannot be signed locally
        return f"https://{self.account_name}.blob.core.windows.net/{container}/{blob_path}"


class LocalStorageService(BaseStorageService):
    """Local development storage adapter providing file isolation and checksums."""

    def __init__(self, base_path: str):
        self.base_path = os.path.abspath(base_path)
        os.makedirs(self.base_path, exist_ok=True)
        logger.warning(
            "Azure Blob credentials not configured. LocalStorageService active at: %s",
            self.base_path,
        )

    @property
    def provider_name(self) -> str:
        return "local_dev"

    def _resolve_safe_path(self, container: str, blob_path: str) -> str:
        clean_container = re.sub(r"[^a-zA-Z0-9_-]", "_", container)
        target_dir = os.path.join(self.base_path, clean_container)
        target_file = os.path.abspath(os.path.join(target_dir, blob_path))

        # Path traversal guard
        if not target_file.startswith(self.base_path):
            raise ValueError(f"Path traversal detected: {blob_path}")

        os.makedirs(os.path.dirname(target_file), exist_ok=True)
        return target_file

    def upload_file(
        self,
        file_obj: BinaryIO,
        container: str,
        blob_path: str,
        content_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        target_file = self._resolve_safe_path(container, blob_path)

        md5 = hashlib.md5()
        sha256 = hashlib.sha256()
        total_bytes = 0

        with open(target_file, "wb") as f_out:
            while True:
                chunk = file_obj.read(1024 * 1024)
                if not chunk:
                    break
                f_out.write(chunk)
                md5.update(chunk)
                sha256.update(chunk)
                total_bytes += len(chunk)

        blob_uri = f"local://{container}/{blob_path}"
        return {
            "provider": self.provider_name,
            "container": container,
            "blob_path": blob_path,
            "blob_uri": blob_uri,
            "file_size_bytes": total_bytes,
            "md5_checksum": md5.hexdigest(),
            "sha256_checksum": sha256.hexdigest(),
            "local_path": target_file,
        }

    def download_file(self, container: str, blob_path: str) -> bytes:
        target_file = self._resolve_safe_path(container, blob_path)
        if not os.path.exists(target_file):
            raise FileNotFoundError(f"Blob not found in local storage: {blob_path}")
        with open(target_file, "rb") as f:
            return f.read()

    def delete_file(self, container: str, blob_path: str) -> bool:
        target_file = self._resolve_safe_path(container, blob_path)
        if os.path.exists(target_file):
            os.remove(target_file)
            return True
        return False

    def file_exists(self, container: str, blob_path: str) -> bool:
        target_file = self._resolve_safe_path(container, blob_path)
        return os.path.exists(target_file)

    def get_access_url(
        self, container: str, blob_path: str, expiry_minutes: int = 60
    ) -> str:
        # Returns simulated local access URI
        return f"/api/v1/ingestion/download/{container}/{blob_path}"


_storage_instance: Optional[BaseStorageService] = None


def get_storage_service() -> BaseStorageService:
    """Factory to retrieve configured storage service instance."""
    global _storage_instance
    if _storage_instance is None:
        conn_str = settings.AZURE_STORAGE_CONNECTION_STRING.strip()
        if conn_str:
            _storage_instance = AzureBlobStorageService(
                connection_string=conn_str,
                account_name=settings.AZURE_STORAGE_ACCOUNT_NAME,
            )
        else:
            if not settings.ALLOW_DEV_LOCAL_STORAGE:
                raise RuntimeError(
                    "AZURE_STORAGE_CONNECTION_STRING is missing and local storage fallback is disabled."
                )
            base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), settings.LOCAL_STORAGE_PATH)
            _storage_instance = LocalStorageService(base_path=base_dir)
    return _storage_instance
