import polars as pl
import numpy as np
from app.analyzers.baseline_runner import baseline_runner
from app.analyzers.task_classifier import TaskClassificationResult
from app.analyzers.validation_engine import ValidationResult, CVStrategy

def test_baseline_runner_regression():
    # Create mock dataset
    np.random.seed(42)
    n = 100
    df = pl.DataFrame({
        "id": range(n),
        "f1": np.random.randn(n),
        "f2": np.random.randn(n),
        "cat1": ["a" if i % 2 == 0 else "b" for i in range(n)],
        "target": np.random.randn(n) * 10
    })

    task_result = TaskClassificationResult(
        target_column="target",
        id_column="id",
        problem_type="Regression"
    )
    
    validation_result = ValidationResult(
        cv_strategy=CVStrategy(strategy_name="KFold", folds=3, reasoning="test"),
        leakage_report={"has_leakage": False, "warnings": []}
    )

    result = baseline_runner.run_baseline(df, task_result, validation_result)
    
    assert result.model_name == "LightGBM"
    assert result.metric_name == "RMSE"
    assert result.cv_score > 0
    assert len(result.feature_importances) == 3 # f1, f2, cat1

def test_baseline_runner_classification():
    # Create mock dataset
    np.random.seed(42)
    n = 100
    df = pl.DataFrame({
        "id": range(n),
        "f1": np.random.randn(n),
        "f2": np.random.randn(n),
        "target": np.random.randint(0, 2, n)
    })

    task_result = TaskClassificationResult(
        target_column="target",
        id_column="id",
        problem_type="Binary Classification"
    )
    
    validation_result = ValidationResult(
        cv_strategy=CVStrategy(strategy_name="StratifiedKFold", folds=3, reasoning="test"),
        leakage_report={"has_leakage": False, "warnings": []}
    )

    result = baseline_runner.run_baseline(df, task_result, validation_result)
    
    assert result.model_name == "LightGBM"
    assert result.metric_name == "Log Loss"
    assert result.cv_score > 0
    assert len(result.feature_importances) == 2
