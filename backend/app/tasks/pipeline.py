"""
Celery-based analysis pipeline task.
Orchestrates: document analysis → data profiling → task classification →
              validation → LLM orchestration → notebook generation → packaging.
Publishes SSE events at each stage so the frontend updates in real time.
"""
import asyncio
import logging
from pathlib import Path

from celery import Celery

from app.core.config import settings

logger = logging.getLogger("app.tasks.pipeline")

celery_app = Celery(
    "competition_pipeline",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)


def _emit(competition_id: str, event: str, data: dict) -> None:
    """Safely emit SSE events from a synchronous Celery worker context."""
    try:
        from app.api.v1.events import publish_event
        loop = asyncio.new_event_loop()
        loop.run_until_complete(asyncio.sleep(0))  # Ensure loop is ready
        publish_event(competition_id, event, data)
        loop.close()
    except Exception as e:
        logger.warning("SSE publish failed (non-critical): %s", e)


@celery_app.task(bind=True, name="pipeline.run_analysis")
def run_analysis_pipeline(self, competition_id: str, file_paths: list[str]) -> dict:
    """
    Full analysis pipeline for a competition. Runs synchronously in a Celery worker.
    Emits SSE events at each stage for real-time frontend updates.
    """
    from app.analyzers.document_rules_extractor import document_rules_extractor
    from app.analyzers.data_profiler import data_profiler
    from app.analyzers.dataset_comparator import dataset_comparator
    from app.analyzers.task_classifier import task_classifier
    from app.analyzers.validation_engine import validation_engine

    paths = [Path(p) for p in file_paths]

    try:
        # Stage 1: Document Analysis
        _emit(competition_id, "stage_start", {"stage": 1, "name": "Document Analysis"})
        doc_files = [p for p in paths if p.suffix.lower() in (".pdf", ".docx", ".txt")]
        document_facts = document_rules_extractor.consolidate_document_facts(doc_files)
        _emit(competition_id, "stage_done", {
            "stage": 1,
            "name": "Document Analysis",
            "metrics_found": len(document_facts.metric_mentions),
            "target_hints": len(document_facts.target_variable_mentions),
        })

        # Stage 2: Data Profiling
        _emit(competition_id, "stage_start", {"stage": 2, "name": "Data Profiling"})
        csv_files = [p for p in paths if p.suffix.lower() in (".csv", ".parquet")]
        train_profile = None
        test_profile = None
        for p in csv_files:
            role = "train" if "train" in p.stem.lower() else "test" if "test" in p.stem.lower() else "unknown"
            profile = data_profiler.profile_file(p, competition_id=competition_id, role=role)
            if role == "train":
                train_profile = profile
            elif role == "test":
                test_profile = profile

        if train_profile is None:
            raise ValueError("No train file found in uploaded paths.")

        _emit(competition_id, "stage_done", {
            "stage": 2, "name": "Data Profiling",
            "train_rows": train_profile.row_count,
            "train_cols": train_profile.column_count,
        })

        # Stage 3: Schema Reconciliation & Drift
        _emit(competition_id, "stage_start", {"stage": 3, "name": "Schema Reconciliation"})
        comparison = dataset_comparator.compare(train_profile, test_profile) if test_profile else None
        _emit(competition_id, "stage_done", {"stage": 3, "name": "Schema Reconciliation"})

        # Stage 4: Task Classification
        _emit(competition_id, "stage_start", {"stage": 4, "name": "Task Classification"})
        from app.analyzers.dataset_comparator import ComparisonReport
        comp_report = comparison or ComparisonReport(schema_differences=[], drift_reports=[], target_candidates=[])
        task_result = task_classifier.classify(document_facts, train_profile, comp_report)
        _emit(competition_id, "stage_done", {
            "stage": 4, "name": "Task Classification",
            "problem_type": task_result.problem_type,
            "target": task_result.target_column,
            "metric": task_result.evaluation_metric,
            "confidence": task_result.confidence_score,
        })

        # Stage 5: Validation Engine
        _emit(competition_id, "stage_start", {"stage": 5, "name": "Validation Engine"})
        val_result = validation_engine.determine_validation(task_result, train_profile, test_profile)
        _emit(competition_id, "stage_done", {
            "stage": 5, "name": "Validation Engine",
            "cv_strategy": val_result.cv_strategy.strategy_name,
            "leakage": val_result.leakage_report.has_leakage,
        })

        # Emit final completed event
        _emit(competition_id, "completed", {
            "problem_type": task_result.problem_type,
            "target": task_result.target_column,
            "metric": task_result.evaluation_metric,
            "cv_strategy": val_result.cv_strategy.strategy_name,
            "leakage": val_result.leakage_report.has_leakage,
        })

        return {
            "competition_id": competition_id,
            "problem_type": task_result.problem_type,
            "target": task_result.target_column,
            "metric": task_result.evaluation_metric,
            "cv_strategy": val_result.cv_strategy.strategy_name,
        }

    except Exception as e:
        logger.error("Pipeline failed for %s: %s", competition_id, e, exc_info=True)
        _emit(competition_id, "failed", {"error": str(e)})
        raise
