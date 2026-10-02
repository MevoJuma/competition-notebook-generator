import json
from app.schemas.document import ExtractedDocumentFacts
from app.schemas.profile import DatasetProfileCreate
from app.analyzers.task_classifier import TaskClassificationResult
from app.analyzers.validation_engine import ValidationResult
from app.llm.contracts import NotebookPlan
from app.llm.client import llm_client

class NotebookOrchestrator:
    """Orchestrates the LLM to synthesize extracted intelligence into a coherent Notebook Plan."""

    @classmethod
    async def synthesize_plan(
        cls,
        competition_name: str,
        task_result: TaskClassificationResult,
        validation_result: ValidationResult,
        train_profile: DatasetProfileCreate,
        document_facts: ExtractedDocumentFacts
    ) -> NotebookPlan:
        
        # Build a highly structured prompt using all gathered intelligence
        prompt = f"""
        Competition: {competition_name}
        
        Task Classification:
        - Problem Type: {task_result.problem_type}
        - Target Variable: {task_result.target_column}
        - ID Column: {task_result.id_column}
        - Evaluation Metric: {task_result.evaluation_metric}
        - Confidence: {task_result.confidence_score}
        
        Validation Engine Output:
        - Strategy: {validation_result.cv_strategy.strategy_name}
        - Folds: {validation_result.cv_strategy.folds}
        - Group Column: {validation_result.cv_strategy.group_column}
        - Time Column: {validation_result.cv_strategy.time_column}
        - Leakage Warnings: {json.dumps(validation_result.leakage_report.warnings)}
        
        Dataset Profile (Train):
        - Rows: {train_profile.row_count}
        - Columns: {train_profile.column_count}
        - Schema: {json.dumps(train_profile.schema_definition)}
        
        Document Rules:
        - Rules: {json.dumps(document_facts.constraints_and_rules)}
        
        Based on this rich, verified context, formulate a complete machine learning notebook plan. 
        Propose at least two relevant feature engineering ideas using standard Pandas/Polars code, 
        and outline a robust modeling strategy (e.g., LightGBM + XGBoost ensemble).
        """
        
        plan = await llm_client.generate_structured(prompt, NotebookPlan)
        return plan

orchestrator = NotebookOrchestrator()
