"""Storage subsystem initialization and factory."""

from clarity.config import settings
from clarity.storage.base import StorageBackend, compute_sha256, get_hashed_storage_path
from clarity.storage.local import LocalStorageBackend
from clarity.storage.s3 import S3StorageBackend


def get_storage() -> StorageBackend:
    """Instantiate configured storage backend (Local or S3/MinIO)."""
    if settings.storage_backend == "s3":
        return S3StorageBackend(
            endpoint_url=settings.s3_endpoint_url,
            access_key=settings.s3_access_key,
            secret_key=settings.s3_secret_key,
            bucket_name=settings.s3_bucket_name,
            region_name=settings.s3_region_name,
        )
    return LocalStorageBackend(base_dir=settings.storage_local_dir)


__all__ = [
    "StorageBackend",
    "LocalStorageBackend",
    "S3StorageBackend",
    "get_storage",
    "compute_sha256",
    "get_hashed_storage_path",
]
