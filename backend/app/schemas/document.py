from typing import List, Optional
from pydantic import BaseModel, Field


class DocumentEvidence(BaseModel):
    """Specific textual snippet providing verifiable evidence for an extracted conclusion."""
    text_snippet: str
    source_file: str
    page_number: Optional[int] = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class ExtractedDocumentFacts(BaseModel):
    """Structured knowledge extracted from competition PDFs, DOCX, and TXT files."""
    competition_title: Optional[str] = None
    problem_objective: Optional[str] = None
    domain: Optional[str] = None
    target_variable_mentions: List[str] = []
    id_column_mentions: List[str] = []
    metric_mentions: List[str] = []
    submission_format_notes: List[str] = []
    constraints_and_rules: List[str] = []
    evidence_snippets: List[DocumentEvidence] = []
    full_text_length: int = 0
