from typing import List, Optional
from pydantic import BaseModel

from app.schemas.document import ExtractedDocumentFacts
from app.schemas.profile import DatasetProfileCreate
from app.analyzers.dataset_comparator import ComparisonReport

class TaskClassificationResult(BaseModel):
    target_column: Optional[str] = None
    id_column: Optional[str] = None
    problem_type: str = "Unknown"  # "Regression", "Binary Classification", "Multiclass Classification"
    evaluation_metric: str = "Unknown"
    confidence_score: float = 0.0
    reasoning: List[str] = []

class CompetitionTaskClassifier:
    """Classifies the competition problem using multi-signal heuristics."""

    @classmethod
    def classify(
        cls, 
        document_facts: ExtractedDocumentFacts, 
        train_profile: DatasetProfileCreate, 
        comparison_report: ComparisonReport
    ) -> TaskClassificationResult:
        
        result = TaskClassificationResult(reasoning=[])
        confidence = 0.0

        # 1. Target Column Identification
        # Highest signal: column missing in test set
        target = None
        if len(comparison_report.target_candidates) == 1:
            target = comparison_report.target_candidates[0]
            result.reasoning.append(f"Target '{target}' inferred uniquely from schema difference (missing in test).")
            confidence += 0.4
        elif document_facts.target_variable_mentions:
            for candidate in document_facts.target_variable_mentions:
                if candidate in train_profile.schema_definition:
                    target = candidate
                    result.reasoning.append(f"Target '{target}' inferred from document analysis and verified in schema.")
                    confidence += 0.4
                    break
        
        if target:
            result.target_column = target
            
            # 2. Problem Type Classification
            target_profile = train_profile.column_profiles.get(target)
            if target_profile:
                if target_profile.dtype in ("String", "Categorical", "Boolean"):
                    if target_profile.unique_count == 2:
                        result.problem_type = "Binary Classification"
                        confidence += 0.3
                    elif target_profile.unique_count and target_profile.unique_count > 2:
                        result.problem_type = "Multiclass Classification"
                        confidence += 0.3
                elif target_profile.dtype in ("Int8", "Int16", "Int32", "Int64", "UInt8", "UInt16", "UInt32", "UInt64"):
                    # Check unique counts to distinguish between classification and regression
                    if target_profile.unique_count == 2:
                        result.problem_type = "Binary Classification"
                        confidence += 0.3
                    elif target_profile.unique_count and target_profile.unique_count <= 20:
                        result.problem_type = "Multiclass Classification"
                        confidence += 0.2
                    else:
                        result.problem_type = "Regression"
                        confidence += 0.2
                else: # Float types
                    result.problem_type = "Regression"
                    confidence += 0.3
        else:
            result.reasoning.append("Could not confidently identify the target column.")

        # 3. ID Column Identification
        id_candidate = None
        if document_facts.id_column_mentions:
            for candidate in document_facts.id_column_mentions:
                if candidate in train_profile.schema_definition:
                    id_candidate = candidate
                    result.reasoning.append(f"ID column '{id_candidate}' inferred from document analysis.")
                    confidence += 0.15
                    break
        
        if not id_candidate:
            # Fallback heuristic 1: common name patterns
            for col in train_profile.schema_definition.keys():
                if col.lower() in ("id", "index", "uniqueid", "unique_id") or col.lower().endswith("_id"):
                    id_candidate = col
                    result.reasoning.append(f"ID column '{id_candidate}' inferred from column name heuristic.")
                    confidence += 0.1
                    break

        if not id_candidate:
            # Fallback heuristic 2: column where unique_count == row_count (true identifier)
            for col, prof in train_profile.column_profiles.items():
                if col != target and prof.unique_count == train_profile.row_count:
                    id_candidate = col
                    result.reasoning.append(f"ID column '{id_candidate}' inferred: unique count equals row count.")
                    confidence += 0.1
                    break
        
        if id_candidate:
            result.id_column = id_candidate

        # 4. Evaluation Metric
        if document_facts.metric_mentions:
            result.evaluation_metric = document_facts.metric_mentions[0]
            result.reasoning.append(f"Metric '{result.evaluation_metric}' inferred from document analysis.")
            confidence += 0.15
        else:
            # Default metrics based on problem type
            if result.problem_type == "Regression":
                result.evaluation_metric = "RMSE"
                result.reasoning.append("Defaulting metric to RMSE for Regression.")
            elif result.problem_type == "Binary Classification":
                result.evaluation_metric = "Log Loss"
                result.reasoning.append("Defaulting metric to Log Loss for Binary Classification.")
            elif result.problem_type == "Multiclass Classification":
                result.evaluation_metric = "Log Loss"
                result.reasoning.append("Defaulting metric to Log Loss for Multiclass Classification.")

        result.confidence_score = min(1.0, confidence)
        return result

task_classifier = CompetitionTaskClassifier()
