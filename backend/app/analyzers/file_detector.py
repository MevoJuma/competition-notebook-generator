import re
from pathlib import Path
from app.models.enums import FileCategory

SUPPORTED_EXTENSIONS = {
    ".csv": "csv",
    ".parquet": "parquet",
    ".pq": "parquet",
    ".xlsx": "xlsx",
    ".xls": "xlsx",
    ".json": "json",
    ".pdf": "pdf",
    ".docx": "docx",
    ".txt": "txt",
    ".zip": "zip",
}


def get_file_type(filename: str) -> str:
    """Detect normalized file extension type, returning 'unknown' if unsupported."""
    ext = Path(filename).suffix.lower()
    return SUPPORTED_EXTENSIONS.get(ext, "unknown")


def is_supported_file(filename: str) -> bool:
    """Check if file has an allowed competition extension."""
    return get_file_type(filename) != "unknown"


def infer_file_category_from_name(filename: str) -> FileCategory:
    """Classify initial file category based on filename heuristics and standard naming conventions."""
    name_lower = Path(filename).stem.lower()
    ext = Path(filename).suffix.lower()

    # Documentation and rules
    if ext in [".pdf", ".docx", ".txt"]:
        if any(term in name_lower for term in ["rule", "guideline", "overview", "description", "problem", "readme"]):
            return FileCategory.DOCUMENTATION_RULES
        if any(term in name_lower for term in ["dict", "variable", "definition", "schema", "meta"]):
            return FileCategory.METADATA_DICTIONARY
        return FileCategory.DOCUMENTATION_RULES

    # Sample submission
    if any(term in name_lower for term in ["sample_sub", "sample_submission", "samplesubmission", "submission", "sub_format"]):
        return FileCategory.SAMPLE_SUBMISSION

    # Train data
    if re.search(r"(^|[_\-\s])train([_\-\s\d]|$)", name_lower):
        return FileCategory.TRAIN_DATA

    # Test data
    if re.search(r"(^|[_\-\s])test([_\-\s\d]|$)", name_lower):
        return FileCategory.TEST_DATA

    # Metadata & Data Dictionaries (tabular/json)
    if any(term in name_lower for term in ["dict", "variable", "metadata", "definition", "column"]):
        return FileCategory.METADATA_DICTIONARY

    # Ancillary / Supplementary
    if any(term in name_lower for term in ["extra", "supp", "supplementary", "additional", "lookup", "geo"]):
        return FileCategory.SUPPLEMENTARY_DATA

    # Fallback based on extension
    if ext in [".csv", ".parquet", ".xlsx", ".json"]:
        return FileCategory.UNKNOWN

    return FileCategory.UNKNOWN
