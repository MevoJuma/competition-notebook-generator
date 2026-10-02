import pytest
from unittest.mock import AsyncMock, patch

from app.llm.orchestrator import orchestrator
from app.llm.contracts import NotebookPlan, FeatureEngineeringIdea, ModelStrategy
from app.analyzers.task_classifier import TaskClassificationResult
from app.analyzers.validation_engine import ValidationResult, CVStrategy, LeakageReport
from app.schemas.profile import DatasetProfileCreate
from app.schemas.document import ExtractedDocumentFacts

@pytest.mark.asyncio
async def test_synthesize_plan():
    task_res = TaskClassificationResult(
        problem_type="Binary Classification",
        target_column="is_fraud",
        id_column="id",
        evaluation_metric="Log Loss",
        confidence_score=0.9
    )
    val_res = ValidationResult(
        cv_strategy=CVStrategy(strategy_name="StratifiedKFold", folds=5, reasoning="Classification task"),
        leakage_report=LeakageReport(has_leakage=False, warnings=[])
    )
    train_prof = DatasetProfileCreate(
        competition_id="1", dataset_name="train.csv", row_count=100, column_count=2, memory_bytes=1000,
        schema_definition={"id": "Int64", "is_fraud": "Int64"},
        column_profiles={}, sample_rows=[]
    )
    docs = ExtractedDocumentFacts()

    mock_plan = NotebookPlan(
        competition_title="Fraud Detection",
        problem_type="Binary Classification",
        evaluation_metric="Log Loss",
        target_variable="is_fraud",
        feature_engineering_ideas=[
            FeatureEngineeringIdea(feature_name="dummy", description="dummy", code_snippet="df['dummy'] = 1")
        ],
        model_strategy=ModelStrategy(models_to_train=["LightGBM"], ensemble_method="None"),
        validation_strategy="StratifiedKFold"
    )

    with patch("app.llm.orchestrator.llm_client.generate_structured", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_plan
        
        plan = await orchestrator.synthesize_plan(
            "Fraud Detection", task_res, val_res, train_prof, docs
        )

        assert plan.competition_title == "Fraud Detection"
        assert plan.target_variable == "is_fraud"
        mock_gen.assert_called_once()
        
        called_prompt = mock_gen.call_args[0][0]
        assert "is_fraud" in called_prompt
        assert "StratifiedKFold" in called_prompt
