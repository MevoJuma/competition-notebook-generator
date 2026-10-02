from typing import Optional
from sqlalchemy import Float, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class CompetitionAnalysis(BaseModel):
    """Synthesized competition intelligence produced by AI Orchestrator and verified data engines."""

    __tablename__ = "competition_analyses"

    competition_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("competitions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    problem_type: Mapped[str] = mapped_column(String(100), nullable=False)
    target_column: Mapped[str] = mapped_column(String(255), nullable=False)
    id_columns: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    train_file_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    test_file_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    sample_sub_file_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    evaluation_metric: Mapped[str] = mapped_column(String(100), nullable=False)
    metric_direction: Mapped[str] = mapped_column(String(20), nullable=False, default="MAXIMIZE")
    validation_strategy: Mapped[str] = mapped_column(String(100), nullable=False)
    cv_strategy_details: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    submission_columns: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    leakage_risks: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    feature_engineering_plan: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    recommended_models: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    confidence_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    reasoning_summary: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    # Relationships
    competition: Mapped["Competition"] = relationship("Competition", back_populates="analysis")
