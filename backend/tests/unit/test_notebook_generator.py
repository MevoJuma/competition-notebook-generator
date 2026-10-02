from pathlib import Path
from app.generators.notebook_generator import notebook_generator
from app.llm.contracts import NotebookPlan, FeatureEngineeringIdea, ModelStrategy

def test_generate_notebook(tmp_path: Path):
    plan = NotebookPlan(
        competition_title="Sales Forecasting",
        problem_type="Regression",
        evaluation_metric="RMSE",
        target_variable="sales",
        feature_engineering_ideas=[
            FeatureEngineeringIdea(
                feature_name="Date Features", 
                description="Extract year, month", 
                code_snippet="df['year'] = df['date'].dt.year"
            )
        ],
        model_strategy=ModelStrategy(models_to_train=["LightGBM"], ensemble_method="None"),
        validation_strategy="TimeSeriesSplit"
    )
    
    nb = notebook_generator.generate(plan)
    
    assert len(nb.cells) == 8
    assert "Sales Forecasting" in nb.cells[0].source
    assert "import pandas as pd" in nb.cells[1].source
    
    out_file = tmp_path / "notebook.ipynb"
    notebook_generator.save(nb, str(out_file))
    
    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "Date Features" in content
    assert "df['year'] = df['date'].dt.year" in content
