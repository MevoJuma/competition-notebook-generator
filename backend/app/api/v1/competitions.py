from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.competition import (
    CompetitionCreate,
    CompetitionDetail,
    CompetitionRead,
    CompetitionUpdate,
)
from app.services.competition_service import competition_service

router = APIRouter(prefix="/competitions", tags=["Competitions"])


@router.post("", response_model=CompetitionRead, status_code=status.HTTP_201_CREATED)
async def create_competition(
    data: CompetitionCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new competition workspace."""
    return await competition_service.create_competition(db, data)


@router.get("", response_model=List[CompetitionRead])
async def list_competitions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List all registered competitions with pagination."""
    return await competition_service.list_competitions(db, skip=skip, limit=limit, status=status)


@router.get("/{competition_id}", response_model=CompetitionDetail)
async def get_competition(
    competition_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get competition details including uploaded files."""
    return await competition_service.get_competition_by_id(db, competition_id)


@router.put("/{competition_id}", response_model=CompetitionRead)
async def update_competition(
    competition_id: str,
    data: CompetitionUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update competition attributes or config overrides."""
    return await competition_service.update_competition(db, competition_id, data)


@router.delete("/{competition_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_competition(
    competition_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a competition, associated database records, and filesystem storage."""
    await competition_service.delete_competition(db, competition_id)
