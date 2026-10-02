import hashlib
import os
import zipfile
from pathlib import Path
from typing import List, NamedTuple

from app.analyzers.file_detector import get_file_type, infer_file_category_from_name, is_supported_file
from app.core.config import settings
from app.core.exceptions import ArchiveSecurityException
from app.core.logging import get_logger
from app.models.enums import FileCategory

logger = get_logger("app.analyzers.archive_inspector")


class ExtractedFile(NamedTuple):
    file_path: Path
    original_name: str
    file_type: str
    category: FileCategory
    file_size_bytes: int
    file_hash: str


class ArchiveInspector:
    """Safely inspects and extracts ZIP archives with decompression bounds and path checks."""

    @staticmethod
    def inspect_and_extract(archive_path: Path, output_dir: Path) -> List[ExtractedFile]:
        """Extracts files safely into output_dir with anti-zip-bomb and path traversal defenses."""
        if not zipfile.is_zipfile(archive_path):
            raise ArchiveSecurityException("File is not a valid ZIP archive.", archive_path.name)

        archive_size = archive_path.stat().st_size
        extracted_files: List[ExtractedFile] = []

        with zipfile.ZipFile(archive_path, "r") as zip_ref:
            # 1. Pre-extraction security scan
            total_uncompressed_size = 0
            infolist = zip_ref.infolist()

            for info in infolist:
                # Disallow directory traversal characters
                cleaned_name = info.filename.replace("\\", "/")
                if ".." in cleaned_name or cleaned_name.startswith("/"):
                    raise ArchiveSecurityException(
                        f"Entry '{info.filename}' contains illegal path traversal components.",
                        archive_path.name,
                    )

                total_uncompressed_size += info.file_size

                # Check max unpacked size limit
                if total_uncompressed_size > settings.MAX_TOTAL_ARCHIVE_SIZE_BYTES:
                    raise ArchiveSecurityException(
                        f"Uncompressed archive size exceeds limit of {settings.MAX_TOTAL_ARCHIVE_SIZE_BYTES} bytes.",
                        archive_path.name,
                    )

            # Check compression ratio (Zip-Bomb defense)
            if archive_size > 0:
                compression_ratio = total_uncompressed_size / archive_size
                if compression_ratio > settings.MAX_ZIP_COMPRESSION_RATIO and total_uncompressed_size > 10 * 1024 * 1024:
                    raise ArchiveSecurityException(
                        f"Suspicious compression ratio of {compression_ratio:.1f}x exceeds allowed {settings.MAX_ZIP_COMPRESSION_RATIO}x threshold.",
                        archive_path.name,
                    )

            # 2. Safe Extraction
            for info in infolist:
                if info.is_dir():
                    continue

                filename = Path(info.filename).name
                if not filename or filename.startswith(".") or filename.startswith("__MACOSX"):
                    continue

                if not is_supported_file(filename):
                    logger.warning("Skipping unsupported file '%s' from archive %s", filename, archive_path.name)
                    continue

                # Target file path inside output_dir
                target_path = (output_dir / filename).resolve()
                if not os.path.commonpath([str(output_dir), str(target_path)]) == str(output_dir):
                    raise ArchiveSecurityException(f"Illegal destination path for '{filename}'", archive_path.name)

                # Extract file contents into memory and write to target
                content = zip_ref.read(info)
                target_path.write_bytes(content)

                file_size = len(content)
                file_hash = hashlib.sha256(content).hexdigest()
                file_type = get_file_type(filename)
                category = infer_file_category_from_name(filename)

                extracted_files.append(
                    ExtractedFile(
                        file_path=target_path,
                        original_name=filename,
                        file_type=file_type,
                        category=category,
                        file_size_bytes=file_size,
                        file_hash=file_hash,
                    )
                )
                logger.info("Extracted '%s' (%s, %d bytes) -> category: %s", filename, file_type, file_size, category.value)

        return extracted_files


archive_inspector = ArchiveInspector()
