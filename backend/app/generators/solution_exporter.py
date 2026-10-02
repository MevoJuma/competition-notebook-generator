import io
import zipfile
from pathlib import Path
from typing import Optional

import nbformat as nbf

from app.llm.contracts import NotebookPlan
from app.analyzers.task_classifier import TaskClassificationResult
from app.generators.notebook_generator import notebook_generator
from app.generators.notebook_validator import notebook_validator, NotebookValidationReport


REQUIREMENTS_TEMPLATE = """\
# Auto-generated requirements for competition notebook
numpy>=1.26.4
pandas>=2.2.1
polars>=0.20.15
matplotlib>=3.8.0
seaborn>=0.13.2
scikit-learn>=1.4.1
lightgbm>=4.3.0
xgboost>=2.0.3
catboost>=1.2.3
nbformat>=5.10.0
"""

README_TEMPLATE = """\
# {competition_title}

> Auto-generated starter notebook by the AI Competition Notebook Platform.

## Task Summary
| Field | Value |
|---|---|
| **Problem Type** | {problem_type} |
| **Target Variable** | {target_variable} |
| **Evaluation Metric** | {evaluation_metric} |
| **Validation Strategy** | {validation_strategy} |

## Getting Started

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Open the notebook:
   ```bash
   jupyter notebook notebook.ipynb
   ```

## Feature Engineering
{feature_list}

## Modeling Strategy
- **Models:** {models}
- **Ensemble:** {ensemble}

---
*Generated automatically. Review and adapt before competition submission.*
"""


class SolutionExporter:
    """Packages the generated notebook into a downloadable ZIP bundle."""

    @classmethod
    def build_bundle(
        cls,
        plan: NotebookPlan,
        output_path: Optional[Path] = None,
    ) -> tuple[bytes, NotebookValidationReport]:
        """
        Generates and validates the notebook, then packages everything into a ZIP.
        Returns (zip_bytes, validation_report).
        """
        # 1. Generate notebook
        nb = notebook_generator.generate(plan)

        # 2. Validate
        validation_report = notebook_validator.validate(nb)

        # 3. Serialize notebook to string
        nb_str = nbf.writes(nb)

        # 4. Build README
        feature_list = "\n".join(
            f"- **{f.feature_name}**: {f.description}"
            for f in plan.feature_engineering_ideas
        )
        readme = README_TEMPLATE.format(
            competition_title=plan.competition_title,
            problem_type=plan.problem_type,
            target_variable=plan.target_variable,
            evaluation_metric=plan.evaluation_metric,
            validation_strategy=plan.validation_strategy,
            feature_list=feature_list,
            models=", ".join(plan.model_strategy.models_to_train),
            ensemble=plan.model_strategy.ensemble_method,
        )

        # 5. Pack everything into an in-memory ZIP
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("notebook.ipynb", nb_str)
            zf.writestr("requirements.txt", REQUIREMENTS_TEMPLATE)
            zf.writestr("README.md", readme)

        zip_bytes = zip_buffer.getvalue()

        # 6. Optionally persist to disk
        if output_path is not None:
            output_path.write_bytes(zip_bytes)

        return zip_bytes, validation_report


solution_exporter = SolutionExporter()
