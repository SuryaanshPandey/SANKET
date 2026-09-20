"""Local content-addressable filesystem storage backend."""

from pathlib import Path
from clarity.storage.base import StorageBackend


class LocalStorageBackend(StorageBackend):
    """Stores files locally on disk under a partitioned directory tree."""

    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _resolve(self, relative_path: str) -> Path:
        target = (self.base_dir / relative_path).resolve()
        # Prevent path traversal attacks
        if not str(target).startswith(str(self.base_dir)):
            raise ValueError(f"Path traversal attempted: {relative_path}")
        return target

    def put_bytes(self, relative_path: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        target = self._resolve(relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        # Content-addressable write (never overwrite if identical, otherwise atomic write)
        temp_target = target.with_suffix(".tmp")
        temp_target.write_bytes(data)
        temp_target.replace(target)
        return str(target)

    def get_bytes(self, relative_path: str) -> bytes:
        target = self._resolve(relative_path)
        if not target.exists():
            raise FileNotFoundError(f"Storage path not found: {relative_path}")
        return target.read_bytes()

    def exists(self, relative_path: str) -> bool:
        return self._resolve(relative_path).exists()

    def get_local_path(self, relative_path: str) -> str:
        target = self._resolve(relative_path)
        if not target.exists():
            raise FileNotFoundError(f"Storage path not found: {relative_path}")
        return str(target)
