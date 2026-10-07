"""
Phase 15: Full End-to-End Synthetic Competition Benchmark
==========================================================
Simulates a complete Zindi-style "Financial Inclusion" competition run:
  1. Generates a realistic synthetic train.csv / test.csv / rules.txt
  2. Runs the full intelligence pipeline (doc analysis → profiling →
     schema reconciliation → classification → validation → baseline)
  3. Synthesises a NotebookPlan (LLM call mocked for determinism)
  4. Generates and validates the notebook
  5. Packages and verifies the ZIP bundle

Every assertion is verifiable against real artefacts — no magic numbers.
"""
import io
import zipfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import numpy as np
import polars as pl
import pytest

# ── Helpers ────────────────────────────────────────────────────────────────

def _make_synthetic_competition(tmp_path: Path) -> dict[str, Path]:
    """Build a minimal but realistic Zindi-style competition fixture."""
    rng = np.random.default_rng(42)
    n_train, n_test = 800, 200

    # --- train.csv
    train_df = pl.DataFrame({
        "uniqueid": [f"id_{i}" for i in range(n_train)],
        "country": rng.choice(["Kenya", "Rwanda", "Tanzania", "Uganda"], n_train).tolist(),
        "year": rng.choice([2016, 2017, 2018], n_train).tolist(),
        "location_type": rng.choice(["Rural", "Urban"], n_train).tolist(),
        "cellphone_access": rng.choice(["Yes", "No"], n_train).tolist(),
        "household_size": rng.integers(1, 12, n_train).tolist(),
        "age_of_respondent": rng.integers(16, 80, n_train).tolist(),
        "gender_of_respondent": rng.choice(["Male", "Female"], n_train).tolist(),
        "bank_account": rng.integers(0, 2, n_train).tolist(),   # binary target
    })

    # --- test.csv  (no target column)
    test_df = pl.DataFrame({
        "uniqueid": [f"id_{n_train + i}" for i in range(n_test)],
        "country": rng.choice(["Kenya", "Rwanda", "Tanzania", "Uganda"], n_test).tolist(),
        "year": rng.choice([2016, 2017, 2018], n_test).tolist(),
        "location_type": rng.choice(["Rural", "Urban"], n_test).tolist(),
        "cellphone_access": rng.choice(["Yes", "No"], n_test).tolist(),
        "household_size": rng.integers(1, 12, n_test).tolist(),
        "age_of_respondent": rng.integers(16, 80, n_test).tolist(),
        "gender_of_respondent": rng.choice(["Male", "Female"], n_test).tolist(),
    })

    # --- rules.txt
    rules_txt = (
        "Financial Inclusion in Africa Challenge.\n\n"
        "Objective: The goal is to predict whether a respondent has a bank_account or not.\n"
        "The unique identifier column is 'uniqueid'.\n"
        "Evaluation metric: ROC-AUC (Area Under the ROC Curve).\n"
        "Limit of 5 submissions per day.\n"
        "No external data is permitted.\n"
    )

    train_path = tmp_path / "train.csv"
    test_path = tmp_path / "test.csv"
    rules_path = tmp_path / "competition_rules.txt"

    train_df.write_csv(str(train_path))
    test_df.write_csv(str(test_path))
    rules_path.write_text(rules_txt, encoding="utf-8")

    return {"train": train_path, "test": test_path, "rules": rules_path}


# ── Benchmark Test ─────────────────────────────────────────────────────────

class TestSyntheticCompetitionBenchmark:

    @pytest.fixture(autouse=True)
    def _paths(self, tmp_path: Path):
        self.paths = _make_synthetic_competition(tmp_path)

    # ------------------------------------------------------------------
    # Stage 1 – Document Analysis
    # ------------------------------------------------------------------
    def test_document_analysis_extracts_correct_facts(self):
        from app.analyzers.document_rules_extractor import document_rules_extractor

        facts = document_rules_extractor.extract_from_file(self.paths["rules"])

        assert "ROC-AUC" in facts.metric_mentions, "Metric not extracted"
        assert any("bank_account" in t for t in facts.target_variable_mentions), \
            "Target 'bank_account' not extracted"
        assert any("uniqueid" in i for i in facts.id_column_mentions), \
            "ID column 'uniqueid' not extracted"
        assert any("5 submissions" in r for r in facts.constraints_and_rules), \
            "Submission limit rule not extracted"

    # ------------------------------------------------------------------
    # Stage 2 – Data Profiling
    # ------------------------------------------------------------------
    def test_data_profiler_train(self):
        from app.analyzers.data_profiler import data_profiler

        profile = data_profiler.profile_file(
            self.paths["train"], competition_id="bench-001", role="train"
        )

        assert profile.row_count == 800
        assert profile.column_count == 9
        assert "bank_account" in profile.schema_definition
        assert "uniqueid" in profile.schema_definition

        target_prof = profile.column_profiles["bank_account"]
        assert target_prof.unique_count == 2, "Binary target must have exactly 2 unique values"
        assert target_prof.null_count == 0

    def test_data_profiler_test(self):
        from app.analyzers.data_profiler import data_profiler

        profile = data_profiler.profile_file(
            self.paths["test"], competition_id="bench-001", role="test"
        )

        assert profile.row_count == 200
        assert "bank_account" not in profile.schema_definition, \
            "Target column must be absent from test set"

    # ------------------------------------------------------------------
    # Stage 3 – Schema Reconciliation & Drift
    # ------------------------------------------------------------------
    def test_schema_reconciliation(self):
        from app.analyzers.data_profiler import data_profiler
        from app.analyzers.dataset_comparator import dataset_comparator

        train = data_profiler.profile_file(self.paths["train"], "bench-001", role="train")
        test = data_profiler.profile_file(self.paths["test"], "bench-001", role="test")
        report = dataset_comparator.compare(train, test)

        assert "bank_account" in report.target_candidates, \
            "Missing target must be detected as candidate"
        missing_in_test = [d for d in report.schema_differences if d.issue == "missing_in_test"]
        assert any(d.column_name == "bank_account" for d in missing_in_test)

    # ------------------------------------------------------------------
    # Stage 4 – Task Classification
    # ------------------------------------------------------------------
    def test_task_classification(self):
        from app.analyzers.data_profiler import data_profiler
        from app.analyzers.dataset_comparator import dataset_comparator
        from app.analyzers.document_rules_extractor import document_rules_extractor
        from app.analyzers.task_classifier import task_classifier

        doc_facts = document_rules_extractor.extract_from_file(self.paths["rules"])
        train = data_profiler.profile_file(self.paths["train"], "bench-001", role="train")
        test = data_profiler.profile_file(self.paths["test"], "bench-001", role="test")
        comp_report = dataset_comparator.compare(train, test)

        result = task_classifier.classify(doc_facts, train, comp_report)

        assert result.target_column == "bank_account"
        assert result.problem_type == "Binary Classification"
        assert result.evaluation_metric == "ROC-AUC"
        assert result.id_column == "uniqueid"
        assert result.confidence_score >= 0.7

    # ------------------------------------------------------------------
    # Stage 5 – Validation Engine
    # ------------------------------------------------------------------
    def test_validation_engine(self):
        from app.analyzers.data_profiler import data_profiler
        from app.analyzers.dataset_comparator import dataset_comparator
        from app.analyzers.document_rules_extractor import document_rules_extractor
        from app.analyzers.task_classifier import task_classifier
        from app.analyzers.validation_engine import validation_engine

        doc_facts = document_rules_extractor.extract_from_file(self.paths["rules"])
        train = data_profiler.profile_file(self.paths["train"], "bench-001", role="train")
        test = data_profiler.profile_file(self.paths["test"], "bench-001", role="test")
        comp_report = dataset_comparator.compare(train, test)
        task_result = task_classifier.classify(doc_facts, train, comp_report)
        val_result = validation_engine.determine_validation(task_result, train, test)

        assert val_result.cv_strategy.strategy_name == "StratifiedKFold", \
            "Binary classification must trigger StratifiedKFold"
        assert val_result.cv_strategy.folds == 5
        assert not val_result.leakage_report.has_leakage, \
            "Clean synthetic split must not raise leakage warning"

    # ------------------------------------------------------------------
    # Stage 6 – Baseline Runner
    # ------------------------------------------------------------------
    def test_baseline_runner(self):
        from app.analyzers.data_profiler import data_profiler
        from app.analyzers.dataset_comparator import dataset_comparator
        from app.analyzers.document_rules_extractor import document_rules_extractor
        from app.analyzers.task_classifier import task_classifier
        from app.analyzers.validation_engine import validation_engine
        from app.analyzers.baseline_runner import baseline_runner

        doc_facts = document_rules_extractor.extract_from_file(self.paths["rules"])
        train_pl = pl.read_csv(str(self.paths["train"]))
        train = data_profiler.profile_file(self.paths["train"], "bench-001", role="train")
        test = data_profiler.profile_file(self.paths["test"], "bench-001", role="test")
        comp_report = dataset_comparator.compare(train, test)
        task_result = task_classifier.classify(doc_facts, train, comp_report)
        val_result = validation_engine.determine_validation(task_result, train, test)

        baseline = baseline_runner.run_baseline(train_pl, task_result, val_result)

        assert baseline.model_name == "LightGBM"
        assert baseline.metric_name == "Log Loss"
        assert 0.0 < baseline.cv_score < 1.0, "Log loss must be a valid positive number"
        assert len(baseline.feature_importances) > 0
        top_feature = baseline.feature_importances[0]
        assert top_feature.importance > 0

    # ------------------------------------------------------------------
    # Stage 7 – Notebook Generation & Validation (LLM mocked)
    # ------------------------------------------------------------------
    @pytest.mark.asyncio
    async def test_notebook_generation_and_bundle(self):
        from app.llm.contracts import NotebookPlan, FeatureEngineeringIdea, ModelStrategy
        from app.generators.notebook_generator import notebook_generator
        from app.generators.notebook_validator import notebook_validator
        from app.generators.solution_exporter import solution_exporter

        plan = NotebookPlan(
            competition_title="Financial Inclusion in Africa",
            problem_type="Binary Classification",
            evaluation_metric="ROC-AUC",
            target_variable="bank_account",
            feature_engineering_ideas=[
                FeatureEngineeringIdea(
                    feature_name="Age Group Buckets",
                    description="Bin age into demographic segments.",
                    code_snippet=(
                        "df['age_group'] = pd.cut("
                        "df['age_of_respondent'], bins=[0,25,35,50,65,100],"
                        " labels=['youth','young_adult','middle','senior','elderly'])"
                    ),
                ),
                FeatureEngineeringIdea(
                    feature_name="Cellphone Access Binary",
                    description="Encode cellphone access as 0/1.",
                    code_snippet="df['cell_binary'] = (df['cellphone_access'] == 'Yes').astype(int)",
                ),
            ],
            model_strategy=ModelStrategy(
                models_to_train=["LightGBM", "CatBoost"],
                ensemble_method="Weighted Average",
            ),
            validation_strategy="StratifiedKFold",
        )

        # Notebook generation
        nb = notebook_generator.generate(plan)
        assert len(nb.cells) > 0

        # Notebook validation
        report = notebook_validator.validate(nb)
        assert report.is_valid, f"Notebook invalid: {report.issues}"

        # Bundle packaging
        zip_bytes, val_report = solution_exporter.build_bundle(plan)
        assert val_report.is_valid

        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            names = zf.namelist()
            assert "notebook.ipynb" in names
            assert "requirements.txt" in names
            assert "README.md" in names

            readme = zf.read("README.md").decode("utf-8")
            assert "Financial Inclusion in Africa" in readme
            assert "ROC-AUC" in readme
            assert "bank_account" in readme
            assert "LightGBM" in readme

    # ------------------------------------------------------------------
    # Stage 8 – Full pipeline determinism (idempotency)
    # ------------------------------------------------------------------
    def test_pipeline_is_deterministic(self):
        """Running the full pipeline twice yields identical results."""
        from app.analyzers.data_profiler import data_profiler
        from app.analyzers.dataset_comparator import dataset_comparator
        from app.analyzers.document_rules_extractor import document_rules_extractor
        from app.analyzers.task_classifier import task_classifier
        from app.analyzers.validation_engine import validation_engine

        def _run():
            doc_facts = document_rules_extractor.extract_from_file(self.paths["rules"])
            train = data_profiler.profile_file(self.paths["train"], "bench-001", role="train")
            test = data_profiler.profile_file(self.paths["test"], "bench-001", role="test")
            comp_report = dataset_comparator.compare(train, test)
            task_result = task_classifier.classify(doc_facts, train, comp_report)
            val_result = validation_engine.determine_validation(task_result, train, test)
            return task_result, val_result

        r1_task, r1_val = _run()
        r2_task, r2_val = _run()

        assert r1_task.target_column == r2_task.target_column
        assert r1_task.problem_type == r2_task.problem_type
        assert r1_task.evaluation_metric == r2_task.evaluation_metric
        assert r1_val.cv_strategy.strategy_name == r2_val.cv_strategy.strategy_name
