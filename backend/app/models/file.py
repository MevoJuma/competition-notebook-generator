from typing import Optional
from sqlalchemy import BigInteger, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.enums import FileCategory


class CompetitionFile(BaseModel):
    """File metadata record tracking uploaded or extracted archives, tabular data, and documents."""

    __tablename__ = "competition_files"

    competition_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("competitions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)  # csv, parquet, pdf, etc.
    category: Mapped[str] = mapped_column(
        String(50),
        default=FileCategory.UNKNOWN.value,
        nullable=False,
        index=True,
    )
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False)  # SHA-256
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, default=dict, nullable=True)

    # Relationships
    competition: Mapped["Competition"] = relationship("Competition", back_populates="files")
    dataset_profile: Mapped[Optional["DatasetProfile"]] = relationship(
        "DatasetProfile",
        back_populates="file",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )
