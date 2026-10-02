import zipfile
import io
from pathlib import Path

from app.generators.solution_exporter import solution_exporter
from app.llm.contracts import NotebookPlan, FeatureEngineeringIdea, ModelStrategy


def _make_plan() -> NotebookPlan:
    return NotebookPlan(
        competition_title="Credit Default Prediction",
        problem_type="Binary Classification",
        evaluation_metric="ROC-AUC",
        target_variable="default",
        feature_engineering_ideas=[
            FeatureEngineeringIdea(
                feature_name="Debt Ratio",
                description="Ratio of debt to income",
                code_snippet="df['debt_ratio'] = df['debt'] / df['income'].clip(lower=1)",
            ),
            FeatureEngineeringIdea(
                feature_name="Credit Utilization",
                description="Outstanding balance divided by credit limit",
                code_snippet="df['utilization'] = df['balance'] / df['limit'].clip(lower=1)",
            ),
        ],
        model_strategy=ModelStrategy(
            models_to_train=["LightGBM", "CatBoost"],
            ensemble_method="Weighted Average",
        ),
        validation_strategy="StratifiedKFold",
    )


def test_bundle_returns_valid_zip():
    plan = _make_plan()
    zip_bytes, report = solution_exporter.build_bundle(plan)

    assert isinstance(zip_bytes, bytes)
    assert len(zip_bytes) > 0

    # Inspect the ZIP contents
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        names = zf.namelist()
        assert "notebook.ipynb" in names
        assert "requirements.txt" in names
        assert "README.md" in names

        readme_text = zf.read("README.md").decode("utf-8")
        assert "Credit Default Prediction" in readme_text
        assert "ROC-AUC" in readme_text
        assert "LightGBM" in readme_text

        req_text = zf.read("requirements.txt").decode("utf-8")
        assert "lightgbm" in req_text


def test_bundle_validation_passes():
    plan = _make_plan()
    _, report = solution_exporter.build_bundle(plan)
    assert report.is_valid is True
    assert len(report.issues) == 0


def test_bundle_persists_to_disk(tmp_path: Path):
    plan = _make_plan()
    out = tmp_path / "solution.zip"
    solution_exporter.build_bundle(plan, output_path=out)
    assert out.exists()
    assert out.stat().st_size > 0
