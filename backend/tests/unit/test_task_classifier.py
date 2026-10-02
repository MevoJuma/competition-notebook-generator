from app.schemas.document import ExtractedDocumentFacts
from app.schemas.profile import DatasetProfileCreate, ColumnProfile
from app.analyzers.dataset_comparator import ComparisonReport
from app.analyzers.task_classifier import task_classifier

def test_task_classifier_regression():
    docs = ExtractedDocumentFacts(metric_mentions=["RMSE"])
    train = DatasetProfileCreate(
        competition_id="comp-1",
        dataset_name="train.csv",
        row_count=100, column_count=3, memory_bytes=1000,
        schema_definition={"id": "Int64", "feature": "Float64", "price": "Float64"},
        column_profiles={
            "id": ColumnProfile(name="id", dtype="Int64"),
            "price": ColumnProfile(name="price", dtype="Float64")
        },
        sample_rows=[]
    )
    comp_report = ComparisonReport(
        schema_differences=[],
        drift_reports=[],
        target_candidates=["price"]
    )

    result = task_classifier.classify(docs, train, comp_report)

    assert result.target_column == "price"
    assert result.problem_type == "Regression"
    assert result.id_column == "id"
    assert result.evaluation_metric == "RMSE"
    assert result.confidence_score >= 0.8

def test_task_classifier_binary():
    docs = ExtractedDocumentFacts(target_variable_mentions=["is_fraud"])
    train = DatasetProfileCreate(
        competition_id="comp-2",
        dataset_name="train.csv",
        row_count=100, column_count=2, memory_bytes=1000,
        schema_definition={"customer_id": "String", "is_fraud": "Int64"},
        column_profiles={
            "customer_id": ColumnProfile(name="customer_id", dtype="String"),
            "is_fraud": ColumnProfile(name="is_fraud", dtype="Int64", unique_count=2)
        },
        sample_rows=[]
    )
    comp_report = ComparisonReport(
        schema_differences=[], drift_reports=[], target_candidates=[]
    )

    result = task_classifier.classify(docs, train, comp_report)

    assert result.target_column == "is_fraud"
    assert result.problem_type == "Binary Classification"
    assert result.id_column == "customer_id"
    assert result.evaluation_metric == "Log Loss" # Defaulted
    assert result.confidence_score >= 0.7
