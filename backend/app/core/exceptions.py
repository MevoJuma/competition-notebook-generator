from typing import Any, Dict, Optional


class CompetitionPlatformException(Exception):
    """Base exception class for all platform domain errors."""

    def __init__(self, message: str, status_code: int = 500, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class EntityNotFoundException(CompetitionPlatformException):
    """Raised when a requested resource (competition, file, notebook, etc.) does not exist."""

    def __init__(self, entity_type: str, entity_id: Any):
        super().__init__(
            message=f"{entity_type} with identifier '{entity_id}' not found.",
            status_code=404,
            details={"entity_type": entity_type, "entity_id": str(entity_id)},
        )


class InvalidFileTypeException(CompetitionPlatformException):
    """Raised when an uploaded file is not in the allowed format whitelist."""

    def __init__(self, filename: str, allowed_types: list[str]):
        super().__init__(
            message=f"File '{filename}' has an unsupported file format. Allowed: {', '.join(allowed_types)}.",
            status_code=400,
            details={"filename": filename, "allowed_types": allowed_types},
        )


class ArchiveSecurityException(CompetitionPlatformException):
    """Raised when an archive violates decompression ratio or contains path traversal entries."""

    def __init__(self, reason: str, filename: str):
        super().__init__(
            message=f"Security violation while processing archive '{filename}': {reason}",
            status_code=400,
            details={"filename": filename, "security_violation": reason},
        )


class DataProfilingException(CompetitionPlatformException):
    """Raised when DuckDB or Polars fails to profile a tabular dataset."""

    def __init__(self, filename: str, reason: str):
        super().__init__(
            message=f"Failed to profile dataset '{filename}': {reason}",
            status_code=422,
            details={"filename": filename, "reason": reason},
        )


class DocumentExtractionException(CompetitionPlatformException):
    """Raised when document parser cannot extract text or metadata."""

    def __init__(self, filename: str, reason: str):
        super().__init__(
            message=f"Failed to extract document contents from '{filename}': {reason}",
            status_code=422,
            details={"filename": filename, "reason": reason},
        )


class TargetDetectionException(CompetitionPlatformException):
    """Raised when target column cannot be resolved with acceptable confidence."""

    def __init__(self, reason: str):
        super().__init__(
            message=f"Target column resolution failed: {reason}",
            status_code=422,
            details={"reason": reason},
        )


class MetricNotSupportedException(CompetitionPlatformException):
    """Raised when evaluation metric is unknown and has no valid fallback."""

    def __init__(self, metric_name: str):
        super().__init__(
            message=f"Evaluation metric '{metric_name}' is not recognized in the platform registry.",
            status_code=400,
            details={"metric_name": metric_name},
        )


class NotebookGenerationException(CompetitionPlatformException):
    """Raised when AST compilation or nbformat generation fails."""

    def __init__(self, section: str, reason: str):
        super().__init__(
            message=f"Notebook generation failed at section '{section}': {reason}",
            status_code=500,
            details={"section": section, "reason": reason},
        )


class NotebookValidationException(CompetitionPlatformException):
    """Raised when generated notebook fails AST syntax check or sandbox dry-run."""

    def __init__(self, stage: str, errors: list[str]):
        super().__init__(
            message=f"Notebook validation failed during '{stage}': {'; '.join(errors)}",
            status_code=422,
            details={"validation_stage": stage, "errors": errors},
        )


class StorageException(CompetitionPlatformException):
    """Raised when file storage operations fail."""

    def __init__(self, operation: str, path: str, error: str):
        super().__init__(
            message=f"Storage operation '{operation}' failed on '{path}': {error}",
            status_code=500,
            details={"operation": operation, "path": path, "error": error},
        )
