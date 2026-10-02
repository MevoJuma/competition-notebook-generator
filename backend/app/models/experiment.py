from typing import List, Optional
from sqlalchemy import Float, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Experiment(BaseModel):
    """Experiment container grouping multiple model evaluation runs."""

    __tablename__ = "experiments"

    competition_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("competitions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="COMPLETED", nullable=False)
    best_cv_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    best_model_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationships
    competition: Mapped["Competition"] = relationship("Competition", back_populates="experiments")
    model_runs: Mapped[List["ModelRun"]] = relationship(
        "ModelRun",
        back_populates="experiment",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class ModelRun(BaseModel):
    """Detailed record for an individual model training run within an experiment."""

    __tablename__ = "model_runs"

    experiment_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    model_family: Mapped[str] = mapped_column(String(50), nullable=False)  # lightgbm, catboost, xgboost, baseline
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    hyperparameters: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    cv_mean_score: Mapped[float] = mapped_column(Float, nullable=False)
    cv_std_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    fold_scores: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    train_time_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    feature_importances: Mapped[Optional[dict]] = mapped_column(JSON, default=dict, nullable=True)

    # Relationships
    experiment: Mapped["Experiment"] = relationship("Experiment", back_populates="model_runs")
