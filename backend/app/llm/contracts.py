from typing import List
from pydantic import BaseModel, Field

class FeatureEngineeringIdea(BaseModel):
    feature_name: str
    description: str
    code_snippet: str = Field(..., description="Pandas/Polars code snippet to generate the feature")

class ModelStrategy(BaseModel):
    models_to_train: List[str] = Field(..., description="List of models, e.g. ['LightGBM', 'CatBoost']")
    ensemble_method: str = Field(..., description="e.g. 'Weighted Average' or 'Stacking'")

class NotebookPlan(BaseModel):
    competition_title: str = Field(..., description="Title of the competition")
    problem_type: str = Field(..., description="E.g., Regression, Binary Classification")
    evaluation_metric: str = Field(..., description="The metric to optimize")
    target_variable: str = Field(..., description="The name of the target column")
    feature_engineering_ideas: List[FeatureEngineeringIdea]
    model_strategy: ModelStrategy
    validation_strategy: str = Field(..., description="The cross-validation strategy to use")
