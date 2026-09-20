"""Abstract storage backend interface."""

from abc import ABC, abstractmethod
import hashlib
from typing import Tuple


class StorageBackend(ABC):
    """Abstract interface for immutable document storage."""

    @abstractmethod
    def put_bytes(self, relative_path: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        """Store bytes at relative_path. Returns the canonical URI/path."""
        pass

    @abstractmethod
    def get_bytes(self, relative_path: str) -> bytes:
        """Retrieve bytes from relative_path."""
        pass

    @abstractmethod
    def exists(self, relative_path: str) -> bool:
        """Check if file exists at relative_path."""
        pass

    @abstractmethod
    def get_local_path(self, relative_path: str) -> str:
        """Ensure file is available on local filesystem and return its absolute path."""
        pass


def compute_sha256(data: bytes) -> str:
    """Compute cryptographic SHA-256 hash of raw untouched bytes."""
    return hashlib.sha256(data).hexdigest()


def get_hashed_storage_path(file_hash: str, prefix: str = "raw", extension: str = "bin") -> str:
    """Generate content-addressable storage path partitioned by hash prefixes."""
    clean_ext = extension.lstrip(".")
    return f"{prefix}/{file_hash[:2]}/{file_hash[2:4]}/{file_hash}.{clean_ext}"
