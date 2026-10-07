from typing import List, Optional
from pydantic import BaseModel
from app.schemas.profile import DatasetProfileCreate
from app.analyzers.task_classifier import TaskClassificationResult

class CVStrategy(BaseModel):
    strategy_name: str
    group_column: Optional[str] = None
    time_column: Optional[str] = None
    folds: int = 5
    reasoning: str

class LeakageReport(BaseModel):
    has_leakage: bool
    warnings: List[str]
    overlapping_ids: int = 0

class ValidationResult(BaseModel):
    cv_strategy: CVStrategy
    leakage_report: LeakageReport

class ValidationEngine:
    """Decides on the CV strategy and detects potential data leakage."""

    @classmethod
    def determine_validation(
        cls, 
        task_result: TaskClassificationResult, 
        train_profile: DatasetProfileCreate,
        test_profile: Optional[DatasetProfileCreate] = None
    ) -> ValidationResult:
        
        # 1. Determine CV Strategy
        strategy_name = "KFold"
        reasoning = "Defaulting to standard KFold for regression task."
        group_col = None
        time_col = None
        
        schema = train_profile.schema_definition
        
        time_candidates = [col for col, dtype in schema.items() if "datetime" in dtype.lower() or "date" in dtype.lower() or "timestamp" in dtype.lower()]
        
        group_candidates = []
        for col, prof in train_profile.column_profiles.items():
            if col != task_result.id_column and col != task_result.target_column:
                if prof.dtype in ("String", "Categorical") and prof.unique_count and 1 < prof.unique_count < 1000:
                    # Exclude high-cardinality columns — they are IDs, not groups
                    if prof.unique_count > train_profile.row_count * 0.1:
                        continue
                    if col.lower().endswith("id") or "group" in col.lower() or "store" in col.lower():
                        group_candidates.append(col)
                        
        if time_candidates:
            strategy_name = "TimeSeriesSplit"
            time_col = time_candidates[0]
            reasoning = f"Detected time column '{time_col}', prioritizing TimeSeriesSplit to prevent future data leakage."
        elif group_candidates:
            strategy_name = "GroupKFold"
            group_col = group_candidates[0]
            reasoning = f"Detected group column '{group_col}', using GroupKFold to ensure disjoint groups."
        elif task_result.problem_type in ("Binary Classification", "Multiclass Classification"):
            strategy_name = "StratifiedKFold"
            reasoning = "Using StratifiedKFold to maintain class balance across folds for classification task."
            
        cv_strategy = CVStrategy(
            strategy_name=strategy_name,
            group_column=group_col,
            time_column=time_col,
            folds=5,
            reasoning=reasoning
        )
        
        # 2. Leakage Checks
        has_leakage = False
        warnings = []
        
        if test_profile and task_result.id_column:
            id_col = task_result.id_column
            train_id_prof = train_profile.column_profiles.get(id_col)
            test_id_prof = test_profile.column_profiles.get(id_col)
            
            if train_id_prof and test_id_prof and train_id_prof.max_value is not None and test_id_prof.min_value is not None:
                if train_id_prof.max_value >= test_id_prof.min_value and train_id_prof.min_value <= test_id_prof.max_value:
                    warnings.append(f"Potential ID overlap detected: Train IDs ({train_id_prof.min_value} to {train_id_prof.max_value}) overlap with Test IDs ({test_id_prof.min_value} to {test_id_prof.max_value}). Verify they are disjoint.")
                    has_leakage = True
                    
        if test_profile and task_result.target_column and task_result.target_column in test_profile.schema_definition:
            warnings.append(f"CRITICAL LEAKAGE: Target column '{task_result.target_column}' is present in the test set!")
            has_leakage = True
            
        leakage_report = LeakageReport(
            has_leakage=has_leakage,
            warnings=warnings
        )
        
        return ValidationResult(cv_strategy=cv_strategy, leakage_report=leakage_report)

validation_engine = ValidationEngine()
