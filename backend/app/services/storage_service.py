import hashlib
import os
import shutil
from pathlib import Path
from typing import BinaryIO, Optional

from app.core.config import settings
from app.core.exceptions import StorageException
from app.core.logging import get_logger

logger = get_logger("app.services.storage")


class StorageService:
    """Service managing workspace file storage with tenant isolation and path validation."""

    def __init__(self, root_dir: Optional[str] = None):
        self.root_dir = Path(root_dir or settings.STORAGE_ROOT).resolve()
        self.upload_dir = Path(settings.STORAGE_UPLOAD_DIR).resolve()
        self.generated_dir = Path(settings.STORAGE_GENERATED_DIR).resolve()
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.generated_dir.mkdir(parents=True, exist_ok=True)

    def get_competition_upload_dir(self, competition_id: str) -> Path:
        """Returns and creates the isolated upload directory for a specific competition."""
        comp_dir = (self.upload_dir / competition_id).resolve()
        # Ensure path does not escape upload directory
        if not self._is_safe_path(self.upload_dir, comp_dir):
            raise StorageException("resolve_path", str(comp_dir), "Path traversal detected.")
        comp_dir.mkdir(parents=True, exist_ok=True)
        return comp_dir

    def get_competition_generated_dir(self, competition_id: str) -> Path:
        """Returns and creates the isolated generated directory for a specific competition."""
        gen_dir = (self.generated_dir / competition_id).resolve()
        if not self._is_safe_path(self.generated_dir, gen_dir):
            raise StorageException("resolve_path", str(gen_dir), "Path traversal detected.")
        gen_dir.mkdir(parents=True, exist_ok=True)
        return gen_dir

    @staticmethod
    def _is_safe_path(base_dir: Path, target_path: Path) -> bool:
        """Verify that target_path is within base_dir using commonpath."""
        try:
            return os.path.commonpath([str(base_dir), str(target_path)]) == str(base_dir)
        except ValueError:
            return False

    def save_file(self, competition_id: str, filename: str, content: bytes) -> tuple[Path, str, int]:
        """Save file bytes to competition workspace, returning (path, sha256_hash, size_bytes)."""
        target_dir = self.get_competition_upload_dir(competition_id)
        # Strip path traversal components from filename
        safe_filename = Path(filename).name
        target_path = (target_dir / safe_filename).resolve()

        if not self._is_safe_path(target_dir, target_path):
            raise StorageException("save_file", str(target_path), "Target path attempts directory traversal.")

        try:
            target_path.write_bytes(content)
            sha256_hash = hashlib.sha256(content).hexdigest()
            size_bytes = len(content)
            logger.info("Saved file '%s' (%d bytes, hash=%s) for competition %s", safe_filename, size_bytes, sha256_hash[:8], competition_id)
            return target_path, sha256_hash, size_bytes
        except Exception as exc:
            raise StorageException("save_file", str(target_path), str(exc)) from exc

    def delete_competition_storage(self, competition_id: str) -> None:
        """Delete all uploaded and generated files associated with a competition."""
        upload_comp_dir = (self.upload_dir / competition_id).resolve()
        if upload_comp_dir.exists() and self._is_safe_path(self.upload_dir, upload_comp_dir):
            shutil.rmtree(upload_comp_dir, ignore_errors=True)

        gen_comp_dir = (self.generated_dir / competition_id).resolve()
        if gen_comp_dir.exists() and self._is_safe_path(self.generated_dir, gen_comp_dir):
            shutil.rmtree(gen_comp_dir, ignore_errors=True)

        logger.info("Purged storage directories for competition %s", competition_id)


storage_service = StorageService()
