from app.schemas.profile import DatasetProfileCreate, ColumnProfile
from app.analyzers.task_classifier import TaskClassificationResult
from app.analyzers.validation_engine import validation_engine

def test_validation_engine_time_series():
    train = DatasetProfileCreate(
        competition_id="comp-1", dataset_name="train.csv", row_count=100, column_count=3, memory_bytes=1000,
        schema_definition={"id": "Int64", "date": "Datetime", "target": "Float64"},
        column_profiles={}, sample_rows=[]
    )
    task_res = TaskClassificationResult(target_column="target", id_column="id", problem_type="Regression")
    
    result = validation_engine.determine_validation(task_res, train)
    assert result.cv_strategy.strategy_name == "TimeSeriesSplit"
    assert result.cv_strategy.time_column == "date"
    assert not result.leakage_report.has_leakage

def test_validation_engine_leakage():
    train = DatasetProfileCreate(
        competition_id="c2", dataset_name="train.csv", row_count=100, column_count=3, memory_bytes=1000,
        schema_definition={"id": "Int64", "target": "Float64"},
        column_profiles={
            "id": ColumnProfile(name="id", dtype="Int64", min_value=1, max_value=100)
        }, sample_rows=[]
    )
    test = DatasetProfileCreate(
        competition_id="c2", dataset_name="test.csv", row_count=50, column_count=3, memory_bytes=1000,
        schema_definition={"id": "Int64", "target": "Float64"},
        column_profiles={
            "id": ColumnProfile(name="id", dtype="Int64", min_value=50, max_value=150)
        }, sample_rows=[]
    )
    task_res = TaskClassificationResult(target_column="target", id_column="id", problem_type="Regression")
    
    result = validation_engine.determine_validation(task_res, train, test)
    assert result.cv_strategy.strategy_name == "KFold"
    assert result.leakage_report.has_leakage
    assert len(result.leakage_report.warnings) == 2
    assert any("Target column 'target' is present" in w for w in result.leakage_report.warnings)
    assert any("Potential ID overlap" in w for w in result.leakage_report.warnings)
