import nbformat as nbf
from app.generators.notebook_validator import notebook_validator

def _make_valid_nb() -> nbf.NotebookNode:
    nb = nbf.v4.new_notebook()
    nb.cells.append(nbf.v4.new_code_cell(
        "import numpy as np\nimport pandas as pd\nimport lightgbm as lgb"
    ))
    nb.cells.append(nbf.v4.new_code_cell("df = pd.DataFrame({'a': [1, 2, 3]})"))
    nb.cells.append(nbf.v4.new_markdown_cell("# Valid notebook"))
    return nb

def _make_invalid_nb() -> nbf.NotebookNode:
    nb = nbf.v4.new_notebook()
    nb.cells.append(nbf.v4.new_code_cell(
        "import numpy as np\nimport pandas as pd"  # missing lightgbm
    ))
    nb.cells.append(nbf.v4.new_code_cell("def bad_syntax(\n    x ="))  # syntax error
    return nb

def test_valid_notebook():
    nb = _make_valid_nb()
    report = notebook_validator.validate(nb)
    assert report.is_valid is True
    assert len(report.issues) == 0

def test_invalid_notebook_syntax():
    nb = _make_invalid_nb()
    report = notebook_validator.validate(nb)
    assert report.is_valid is False
    syntax_issues = [i for i in report.issues if i.issue_type == "syntax_error"]
    assert len(syntax_issues) >= 1
    assert "SyntaxError" in syntax_issues[0].message

def test_missing_import():
    nb = nbf.v4.new_notebook()
    nb.cells.append(nbf.v4.new_code_cell(
        "import numpy as np\nimport pandas as pd\n# lightgbm not imported"
    ))
    report = notebook_validator.validate(nb)
    missing = [i for i in report.issues if i.issue_type == "missing_import"]
    assert len(missing) == 1
    assert "lightgbm" in missing[0].message
