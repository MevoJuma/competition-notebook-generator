from app.schemas.profile import DatasetProfileCreate, ColumnProfile
from app.analyzers.dataset_comparator import dataset_comparator

def test_dataset_comparator():
    train = DatasetProfileCreate(
        competition_id="comp-1",
        dataset_name="train.csv",
        role="train",
        row_count=100,
        column_count=3,
        memory_bytes=1000,
        schema_definition={"id": "Int64", "feature_1": "Float64", "target": "Int64"},
        column_profiles={
            "id": ColumnProfile(name="id", dtype="Int64"),
            "feature_1": ColumnProfile(name="feature_1", dtype="Float64", mean_value=10.0),
            "target": ColumnProfile(name="target", dtype="Int64")
        },
        sample_rows=[]
    )

    test = DatasetProfileCreate(
        competition_id="comp-1",
        dataset_name="test.csv",
        role="test",
        row_count=50,
        column_count=2,
        memory_bytes=500,
        schema_definition={"id": "Int64", "feature_1": "Float64", "extra_col": "String"},
        column_profiles={
            "id": ColumnProfile(name="id", dtype="Int64"),
            "feature_1": ColumnProfile(name="feature_1", dtype="Float64", mean_value=15.0), # Drifted!
            "extra_col": ColumnProfile(name="extra_col", dtype="String")
        },
        sample_rows=[]
    )

    report = dataset_comparator.compare(train, test)

    assert "target" in report.target_candidates
    
    # Missing in test
    assert any(d.column_name == "target" and d.issue == "missing_in_test" for d in report.schema_differences)
    # Missing in train
    assert any(d.column_name == "extra_col" and d.issue == "missing_in_train" for d in report.schema_differences)
    
    # Drift
    assert len(report.drift_reports) == 1
    assert report.drift_reports[0].column_name == "feature_1"
    assert report.drift_reports[0].drift_score == 0.5  # (15 - 10) / 10
