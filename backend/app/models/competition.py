from typing import List, Optional
from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.enums import CompetitionPlatform, CompetitionStatus


class Competition(BaseModel):
    """Competition workspace entity containing all uploaded assets, analyses, and generated notebooks."""

    __tablename__ = "competitions"

    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    platform: Mapped[str] = mapped_column(
        String(50),
        default=CompetitionPlatform.ZINDI.value,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default=CompetitionStatus.UPLOADED.value,
        nullable=False,
        index=True,
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    config_overrides: Mapped[Optional[dict]] = mapped_column(JSON, default=dict, nullable=True)

    # Relationships
    files: Mapped[List["CompetitionFile"]] = relationship(
        "CompetitionFile",
        back_populates="competition",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    dataset_profiles: Mapped[List["DatasetProfile"]] = relationship(
        "DatasetProfile",
        back_populates="competition",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    analysis: Mapped[Optional["CompetitionAnalysis"]] = relationship(
        "CompetitionAnalysis",
        back_populates="competition",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    experiments: Mapped[List["Experiment"]] = relationship(
        "Experiment",
        back_populates="competition",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    notebooks: Mapped[List["Notebook"]] = relationship(
        "Notebook",
        back_populates="competition",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="competition",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
