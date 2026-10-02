import polars as pl
import numpy as np
from typing import List
from pydantic import BaseModel
from sklearn.model_selection import KFold, StratifiedKFold
import lightgbm as lgb
from sklearn.metrics import mean_squared_error, log_loss

from app.analyzers.task_classifier import TaskClassificationResult
from app.analyzers.validation_engine import ValidationResult

class FeatureImportance(BaseModel):
    feature: str
    importance: float

class BaselineResult(BaseModel):
    model_name: str
    cv_score: float
    metric_name: str
    feature_importances: List[FeatureImportance]

class BaselineRunner:
    """Runs a quick LightGBM baseline to extract CV scores and feature importances."""

    @classmethod
    def run_baseline(
        cls, 
        df: pl.DataFrame,
        task_result: TaskClassificationResult,
        validation_result: ValidationResult
    ) -> BaselineResult:
        
        target = task_result.target_column
        features = [c for c in df.columns if c != target and c != task_result.id_column]
        
        X = df.select(features).to_pandas()
        y = df.select(target).to_series().to_numpy()

        cat_features = [c for c in features if df[c].dtype == pl.String or df[c].dtype == pl.Categorical]
        for c in cat_features:
            X[c] = X[c].astype('category')

        n_splits = min(3, validation_result.cv_strategy.folds)
        
        if task_result.problem_type in ("Binary Classification", "Multiclass Classification"):
            kf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
            objective = "binary" if task_result.problem_type == "Binary Classification" else "multiclass"
            metric = "binary_logloss" if objective == "binary" else "multi_logloss"
        else:
            kf = KFold(n_splits=n_splits, shuffle=True, random_state=42)
            objective = "regression"
            metric = "rmse"

        scores = []
        feature_importance_dict = {f: 0.0 for f in features}

        params = {
            "objective": objective,
            "metric": metric,
            "verbose": -1,
            "n_estimators": 10  # Very small for quick baseline profiling
        }

        for train_idx, val_idx in kf.split(X, y):
            X_train, y_train = X.iloc[train_idx], y[train_idx]
            X_val, y_val = X.iloc[val_idx], y[val_idx]
            
            if objective == "regression":
                model = lgb.LGBMRegressor(**params)
                model.fit(X_train, y_train)
                preds = model.predict(X_val)
                score = np.sqrt(mean_squared_error(y_val, preds))
            else:
                model = lgb.LGBMClassifier(**params)
                model.fit(X_train, y_train)
                preds = model.predict_proba(X_val)
                if objective == "binary":
                    # For binary, log_loss needs 1D probabilities for positive class or 2D. 
                    # LGBM predict_proba returns 2D. 
                    score = log_loss(y_val, preds)
                else:
                    score = log_loss(y_val, preds)
                
            scores.append(score)
            
            for i, f in enumerate(features):
                feature_importance_dict[f] += model.feature_importances_[i] / n_splits
                
        importances = [FeatureImportance(feature=k, importance=float(v)) for k, v in feature_importance_dict.items()]
        importances.sort(key=lambda x: x.importance, reverse=True)
        
        return BaselineResult(
            model_name="LightGBM",
            cv_score=float(np.mean(scores)),
            metric_name="RMSE" if objective == "regression" else "Log Loss",
            feature_importances=importances[:10]
        )

baseline_runner = BaselineRunner()
