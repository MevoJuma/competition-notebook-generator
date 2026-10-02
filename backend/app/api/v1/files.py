from typing import List, Optional
from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.file import CompetitionFileRead, CompetitionFileUpdate
from app.services.file_service import file_service

router = APIRouter(prefix="/competitions/{competition_id}/files", tags=["Files"])


@router.post("", response_model=List[CompetitionFileRead], status_code=status.HTTP_201_CREATED)
async def upload_files(
    competition_id: str,
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload multiple files or ZIP archives to the competition workspace."""
    return await file_service.upload_files(db, competition_id, files)


@router.get("", response_model=List[CompetitionFileRead])
async def list_files(
    competition_id: str,
    category: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List all files uploaded or extracted for a competition."""
    return await file_service.list_files_for_competition(db, competition_id, category=category)


@router.get("/{file_id}", response_model=CompetitionFileRead)
async def get_file(
    competition_id: str,
    file_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get metadata for an individual file."""
    return await file_service.get_file_by_id(db, file_id)


@router.patch("/{file_id}", response_model=CompetitionFileRead)
async def update_file(
    competition_id: str,
    file_id: str,
    data: CompetitionFileUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update file category or metadata."""
    return await file_service.update_file(db, file_id, data)


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    competition_id: str,
    file_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a file from the database and storage."""
    await file_service.delete_file(db, file_id)
