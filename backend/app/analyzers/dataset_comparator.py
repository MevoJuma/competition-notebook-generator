from typing import List, Optional
from pydantic import BaseModel

from app.schemas.profile import DatasetProfileCreate

class SchemaDifference(BaseModel):
    column_name: str
    issue: str  # "missing_in_test", "missing_in_train", "type_mismatch"
    train_type: Optional[str] = None
    test_type: Optional[str] = None

class DriftReport(BaseModel):
    column_name: str
    drift_score: float
    warning: Optional[str] = None

class ComparisonReport(BaseModel):
    schema_differences: List[SchemaDifference]
    drift_reports: List[DriftReport]
    target_candidates: List[str]

class DatasetComparator:
    """Analyzes differences between train and test profiles (schema, drift)."""

    @classmethod
    def compare(cls, train_profile: DatasetProfileCreate, test_profile: DatasetProfileCreate) -> ComparisonReport:
        schema_diffs = []
        drift_reports = []
        target_candidates = []

        train_cols = set(train_profile.schema_definition.keys())
        test_cols = set(test_profile.schema_definition.keys())

        # Missing in test (likely target)
        for col in train_cols - test_cols:
            schema_diffs.append(SchemaDifference(
                column_name=col, 
                issue="missing_in_test",
                train_type=train_profile.schema_definition[col]
            ))
            target_candidates.append(col)
            
        # Missing in train
        for col in test_cols - train_cols:
            schema_diffs.append(SchemaDifference(
                column_name=col, 
                issue="missing_in_train",
                test_type=test_profile.schema_definition[col]
            ))

        # Common columns
        common_cols = train_cols & test_cols
        for col in common_cols:
            train_type = train_profile.schema_definition[col]
            test_type = test_profile.schema_definition[col]
            
            # Allow some flexibility between integer sizes or float sizes, but for simplicity strict match here,
            # or a simple heuristic:
            if train_type != test_type:
                # E.g. train is Float64, test is Int64 (could happen if test has no decimals)
                schema_diffs.append(SchemaDifference(
                    column_name=col,
                    issue="type_mismatch",
                    train_type=train_type,
                    test_type=test_type
                ))
            
            # Simple drift detection
            train_col_prof = train_profile.column_profiles.get(col)
            test_col_prof = test_profile.column_profiles.get(col)
            
            if train_col_prof and test_col_prof:
                if train_col_prof.mean_value is not None and test_col_prof.mean_value is not None:
                    train_mean = train_col_prof.mean_value
                    test_mean = test_col_prof.mean_value
                    if train_mean != 0:
                        drift = abs(train_mean - test_mean) / abs(train_mean)
                        # Flag if > 20% shift
                        if drift > 0.20:
                            drift_reports.append(DriftReport(
                                column_name=col,
                                drift_score=drift,
                                warning=f"Significant mean shift detected: train={train_mean:.2f}, test={test_mean:.2f}"
                            ))

        return ComparisonReport(
            schema_differences=schema_diffs,
            drift_reports=drift_reports,
            target_candidates=target_candidates
        )

dataset_comparator = DatasetComparator()
