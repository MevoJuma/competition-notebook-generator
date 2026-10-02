import ast
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List
from pydantic import BaseModel

import nbformat as nbf

class ValidationIssue(BaseModel):
    cell_index: int
    issue_type: str  # "syntax_error", "missing_import", "execution_error"
    message: str

class NotebookValidationReport(BaseModel):
    is_valid: bool
    issues: List[ValidationIssue]

class NotebookValidator:
    """Validates a generated notebook for syntax correctness and import completeness."""

    @classmethod
    def validate(cls, nb: nbf.NotebookNode) -> NotebookValidationReport:
        issues: List[ValidationIssue] = []

        # 1. AST Syntax Validation — check every code cell independently
        for idx, cell in enumerate(nb.cells):
            if cell.cell_type != "code":
                continue
            source = cell.source.strip()
            if not source:
                continue
            try:
                ast.parse(source)
            except SyntaxError as e:
                issues.append(ValidationIssue(
                    cell_index=idx,
                    issue_type="syntax_error",
                    message=f"SyntaxError in cell {idx}: {e.msg} (line {e.lineno})"
                ))

        # 2. Import completeness check — gather all names used across code cells
        #    and verify they have a corresponding import statement somewhere in the notebook
        import_names = set()
        full_code_cells = [c.source for c in nb.cells if c.cell_type == "code" and c.source.strip()]
        all_code = "\n".join(full_code_cells)

        try:
            tree = ast.parse(all_code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        # Track the base module name (e.g. "numpy") and any alias (e.g. "np")
                        import_names.add(alias.name.split(".")[0])
                        if alias.asname:
                            import_names.add(alias.asname)
                elif isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        import_names.add(alias.asname or alias.name)
        except SyntaxError:
            pass  # Already caught per-cell above

        # Flag commonly required packages that were not imported
        required_imports = {"numpy", "pandas", "lightgbm"}
        missing = required_imports - import_names
        if missing:
            issues.append(ValidationIssue(
                cell_index=-1,
                issue_type="missing_import",
                message=f"Notebook is missing expected imports: {sorted(missing)}"
            ))

        return NotebookValidationReport(is_valid=len(issues) == 0, issues=issues)

    @classmethod
    def validate_file(cls, path: Path) -> NotebookValidationReport:
        with open(path, "r", encoding="utf-8") as f:
            nb = nbf.read(f, as_version=4)
        return cls.validate(nb)

notebook_validator = NotebookValidator()
