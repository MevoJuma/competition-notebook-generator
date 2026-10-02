from typing import List, Optional
from sqlalchemy import Boolean, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.enums import NotebookStatus


class Notebook(BaseModel):
    """Jupyter notebook artifact generated for a competition."""

    __tablename__ = "notebooks"

    competition_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("competitions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50),
        default=NotebookStatus.GENERATED.value,
        nullable=False,
    )
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    bundle_storage_path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    structure_manifest: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    syntax_valid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    execution_valid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    submission_valid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    competition: Mapped["Competition"] = relationship("Competition", back_populates="notebooks")
    executions: Mapped[List["NotebookExecution"]] = relationship(
        "NotebookExecution",
        back_populates="notebook",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class NotebookExecution(BaseModel):
    """Validation dry-run execution trace and sandbox output."""

    __tablename__ = "notebook_executions"

    notebook_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("notebooks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    execution_status: Mapped[str] = mapped_column(String(50), nullable=False)  # SUCCESS, FAILED
    cells_executed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_cells: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    runtime_seconds: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    execution_log: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_traceback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    notebook: Mapped["Notebook"] = relationship("Notebook", back_populates="executions")
