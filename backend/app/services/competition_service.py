import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import EntityNotFoundException
from app.core.logging import get_logger
from app.models.competition import Competition
from app.models.enums import CompetitionStatus
from app.schemas.competition import CompetitionCreate, CompetitionUpdate
from app.services.storage_service import storage_service

logger = get_logger("app.services.competition")


class CompetitionService:
    """Service handling competition lifecycle operations."""

    async def create_competition(self, db: AsyncSession, data: CompetitionCreate) -> Competition:
        """Create a new competition workspace."""
        # Ensure slug uniqueness
        base_slug = data.slug or "competition"
        slug = base_slug
        counter = 1
        while True:
            existing = await db.execute(select(Competition).where(Competition.slug == slug))
            if existing.scalar_one_or_none() is None:
                break
            slug = f"{base_slug}-{counter}"
            counter += 1

        comp = Competition(
            id=str(uuid.uuid4()),
            title=data.title,
            slug=slug,
            platform=data.platform,
            status=CompetitionStatus.UPLOADED.value,
            description=data.description,
            config_overrides=data.config_overrides or {},
        )
        db.add(comp)
        await db.commit()
        await db.refresh(comp)

        # Ensure isolated storage directory exists
        storage_service.get_competition_upload_dir(comp.id)
        storage_service.get_competition_generated_dir(comp.id)

        logger.info("Created competition workspace '%s' (ID: %s, Slug: %s)", comp.title, comp.id, comp.slug)
        return comp

    async def get_competition_by_id(self, db: AsyncSession, competition_id: str) -> Competition:
        """Fetch competition with relationships eager-loaded, raising EntityNotFoundException if missing."""
        result = await db.execute(
            select(Competition)
            .options(selectinload(Competition.files))
            .where(Competition.id == competition_id)
        )
        comp = result.scalar_one_or_none()
        if not comp:
            raise EntityNotFoundException("Competition", competition_id)
        return comp

    async def list_competitions(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 50,
        status: Optional[str] = None,
    ) -> List[Competition]:
        """List competitions with optional status filter and pagination."""
        query = select(Competition).options(selectinload(Competition.files)).order_by(Competition.created_at.desc())
        if status:
            query = query.where(Competition.status == status)
        query = query.offset(skip).limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def update_competition(self, db: AsyncSession, competition_id: str, data: CompetitionUpdate) -> Competition:
        """Update competition attributes."""
        comp = await self.get_competition_by_id(db, competition_id)
        update_dict = data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(comp, key, value)

        await db.commit()
        await db.refresh(comp)
        logger.info("Updated competition %s attributes: %s", competition_id, list(update_dict.keys()))
        return comp

    async def update_status(self, db: AsyncSession, competition_id: str, status: CompetitionStatus) -> Competition:
        """Update competition status state."""
        comp = await self.get_competition_by_id(db, competition_id)
        comp.status = status.value
        await db.commit()
        await db.refresh(comp)
        logger.info("Transitioned competition %s status to %s", competition_id, status.value)
        return comp

    async def delete_competition(self, db: AsyncSession, competition_id: str) -> None:
        """Delete competition, database cascades, and associated filesystem storage."""
        comp = await self.get_competition_by_id(db, competition_id)
        await db.delete(comp)
        await db.commit()

        # Clean storage files
        storage_service.delete_competition_storage(competition_id)
        logger.info("Deleted competition workspace %s and associated storage.", competition_id)


competition_service = CompetitionService()
