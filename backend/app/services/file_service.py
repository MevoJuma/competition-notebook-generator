import uuid
from pathlib import Path
from typing import List, Optional
from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analyzers.archive_inspector import archive_inspector
from app.analyzers.file_detector import get_file_type, infer_file_category_from_name, is_supported_file
from app.core.config import settings
from app.core.exceptions import EntityNotFoundException, InvalidFileTypeException, StorageException
from app.core.logging import get_logger
from app.models.file import CompetitionFile
from app.models.enums import FileCategory
from app.schemas.file import CompetitionFileUpdate
from app.services.storage_service import storage_service

logger = get_logger("app.services.file")


class FileService:
    """Service handling file upload, extraction, categorization, and persistence."""

    async def upload_files(
        self,
        db: AsyncSession,
        competition_id: str,
        files: List[UploadFile],
    ) -> List[CompetitionFile]:
        """Upload one or more competition files, extracting ZIP archives safely."""
        created_files: List[CompetitionFile] = []
        upload_dir = storage_service.get_competition_upload_dir(competition_id)

        for upload in files:
            filename = upload.filename or "unknown_file"
            if not is_supported_file(filename):
                raise InvalidFileTypeException(filename, list(archive_inspector.inspect_and_extract.__annotations__.keys()))

            content = await upload.read()
            if len(content) > settings.MAX_UPLOAD_SIZE_BYTES:
                raise StorageException("upload", filename, f"File size exceeds maximum {settings.MAX_UPLOAD_SIZE_BYTES} bytes.")

            file_type = get_file_type(filename)

            # Check if file is a ZIP archive
            if file_type == "zip":
                logger.info("Processing ZIP archive upload '%s' for competition %s", filename, competition_id)
                # First save the raw ZIP
                zip_path, zip_hash, zip_size = storage_service.save_file(competition_id, filename, content)
                zip_record = CompetitionFile(
                    id=str(uuid.uuid4()),
                    competition_id=competition_id,
                    filename=zip_path.name,
                    original_name=filename,
                    file_type="zip",
                    category=FileCategory.SUPPLEMENTARY_DATA.value,
                    file_size_bytes=zip_size,
                    file_hash=zip_hash,
                    storage_path=str(zip_path),
                    metadata_json={"is_archive": True},
                )
                db.add(zip_record)
                created_files.append(zip_record)

                # Now extract files safely
                extracted = archive_inspector.inspect_and_extract(zip_path, upload_dir)
                for item in extracted:
                    extracted_record = CompetitionFile(
                        id=str(uuid.uuid4()),
                        competition_id=competition_id,
                        filename=item.file_path.name,
                        original_name=item.original_name,
                        file_type=item.file_type,
                        category=item.category.value,
                        file_size_bytes=item.file_size_bytes,
                        file_hash=item.file_hash,
                        storage_path=str(item.file_path),
                        metadata_json={"extracted_from_archive": filename},
                    )
                    db.add(extracted_record)
                    created_files.append(extracted_record)

            else:
                # Regular supported file
                saved_path, file_hash, file_size = storage_service.save_file(competition_id, filename, content)
                category = infer_file_category_from_name(filename)

                file_record = CompetitionFile(
                    id=str(uuid.uuid4()),
                    competition_id=competition_id,
                    filename=saved_path.name,
                    original_name=filename,
                    file_type=file_type,
                    category=category.value,
                    file_size_bytes=file_size,
                    file_hash=file_hash,
                    storage_path=str(saved_path),
                    metadata_json={},
                )
                db.add(file_record)
                created_files.append(file_record)

        await db.commit()
        for f in created_files:
            await db.refresh(f)

        logger.info("Successfully ingested %d files for competition %s", len(created_files), competition_id)
        return created_files

    async def list_files_for_competition(
        self,
        db: AsyncSession,
        competition_id: str,
        category: Optional[str] = None,
    ) -> List[CompetitionFile]:
        """Fetch all files associated with a competition."""
        query = select(CompetitionFile).where(CompetitionFile.competition_id == competition_id)
        if category:
            query = query.where(CompetitionFile.category == category)
        query = query.order_by(CompetitionFile.created_at.asc())

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_file_by_id(self, db: AsyncSession, file_id: str) -> CompetitionFile:
        """Fetch file record by id."""
        result = await db.execute(select(CompetitionFile).where(CompetitionFile.id == file_id))
        file_record = result.scalar_one_or_none()
        if not file_record:
            raise EntityNotFoundException("CompetitionFile", file_id)
        return file_record

    async def update_file(
        self,
        db: AsyncSession,
        file_id: str,
        data: CompetitionFileUpdate,
    ) -> CompetitionFile:
        """Update file category or metadata."""
        file_record = await self.get_file_by_id(db, file_id)
        update_dict = data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(file_record, key, value)

        await db.commit()
        await db.refresh(file_record)
        return file_record

    async def delete_file(self, db: AsyncSession, file_id: str) -> None:
        """Delete file from database and remove from storage."""
        file_record = await self.get_file_by_id(db, file_id)
        path = Path(file_record.storage_path)
        if path.exists():
            path.unlink(missing_ok=True)

        await db.delete(file_record)
        await db.commit()
        logger.info("Deleted file %s (%s)", file_record.filename, file_id)


file_service = FileService()
