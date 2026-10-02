from typing import Optional
from sqlalchemy import BigInteger, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class DatasetProfile(BaseModel):
    """Programmatic profiling metadata computed via DuckDB and Polars."""

    __tablename__ = "dataset_profiles"

    competition_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("competitions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("competition_files.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    dataset_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="unknown")  # train, test, sample_sub
    row_count: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    column_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    memory_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)

    # Structured column profiles (dtypes, nulls, unique count, min/max/mean/quantiles)
    schema_definition: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    column_profiles: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    sample_rows: Mapped[Optional[dict]] = mapped_column(JSON, default=list, nullable=True)

    # Relationships
    competition: Mapped["Competition"] = relationship("Competition", back_populates="dataset_profiles")
    file: Mapped[Optional["CompetitionFile"]] = relationship("CompetitionFile", back_populates="dataset_profile")
