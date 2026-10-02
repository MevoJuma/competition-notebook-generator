import re
from pathlib import Path
from typing import List, Tuple

from app.analyzers.document_analyzer import document_text_extractor
from app.core.logging import get_logger
from app.schemas.document import DocumentEvidence, ExtractedDocumentFacts

logger = get_logger("app.analyzers.document_rules_extractor")

# Metric matching patterns with standardized canonical names
METRIC_PATTERNS = [
    (r"\b(roc[-_\s]?auc|area under (?:the )?(?:roc )?curve)\b", "ROC-AUC"),
    (r"\b(log[-_\s]?loss|logarithmic loss|cross[-_\s]?entropy)\b", "Log Loss"),
    (r"\b(f1[-_\s]?macro|macro[-_\s]?f1)\b", "F1-Macro"),
    (r"\b(f1[-_\s]?micro|micro[-_\s]?f1)\b", "F1-Micro"),
    (r"\b(f1[-_\s]?weighted|weighted[-_\s]?f1)\b", "F1-Weighted"),
    (r"\b(f1[-_\s]?(?:score)?)\b", "F1-Score"),
    (r"\b(rmse|root mean square[d]? error)\b", "RMSE"),
    (r"\b(rmsle|root mean square[d]? log(?:arithmic)? error)\b", "RMSLE"),
    (r"\b(mae|mean absolute error)\b", "MAE"),
    (r"\b(mape|mean absolute percentage error)\b", "MAPE"),
    (r"\b(accuracy)\b", "Accuracy"),
    (r"\b(cohen(?:'s)? kappa|quadratic weighted kappa|qwk)\b", "Quadratic Weighted Kappa"),
    (r"\b(matthews correlation coefficient|mcc)\b", "MCC"),
    (r"\b(pr[-_\s]?auc|precision[-_\s]?recall auc|average precision)\b", "PR-AUC"),
    (r"\b(ndcg(?:@\d+)?)\b", "NDCG"),
    (r"\b(map@\d+|mean average precision)\b", "MAP@K"),
    (r"\b(r2|r-squared|coefficient of determination)\b", "R2"),
]

TARGET_PATTERNS = [
    r"(?:target variable|target column|dependent variable|column to predict|predict the value of)\s*(?:is|:)?\s*['\"`]?([a-zA-Z0-9_\-]+)['\"`]?",
    r"(?:goal is to predict|task is to predict|objective is to predict)\s*(?:whether\s+)?['\"`]?([a-zA-Z0-9_\-]+)['\"`]?",
    r"(?:predict(?:ing)?)\s+['\"`]?([a-zA-Z0-9_]{3,30})['\"`]?\s+(?:for each|based on|given)",
]

ID_PATTERNS = [
    r"(?:unique identifier|identifier column|id column|primary key|unique id)\s*(?:is|:)?\s*['\"`]?([a-zA-Z0-9_\-]+)['\"`]?",
    r"(?:each row is identified by|identified uniquely by)\s*['\"`]?([a-zA-Z0-9_\-]+)['\"`]?",
]

RULE_PATTERNS = [
    r"((?:external data|pre-trained models|leakage|private sharing|code requirements)[^\.\n]+[\.\n])",
    r"((?:maximum of|limit of)\s*\d+\s*submissions?\s*(?:per day)?[\.\n])",
]


class DocumentRulesExtractor:
    """Analyzes text chunks to extract competition facts, evaluation metrics, and evidence snippets."""

    @classmethod
    def extract_from_file(cls, file_path: Path) -> ExtractedDocumentFacts:
        """Extract facts and evidence from a document file."""
        chunks = document_text_extractor.extract_text_with_pages(file_path)
        full_text = "\n\n".join(text for text, _ in chunks)
        facts = ExtractedDocumentFacts(full_text_length=len(full_text))

        evidence_list: List[DocumentEvidence] = []
        filename = file_path.name

        # 1. Metric Mentions
        found_metrics = set()
        for regex, canonical_metric in METRIC_PATTERNS:
            for text, page in chunks:
                match = re.search(regex, text, re.IGNORECASE)
                if match and canonical_metric not in found_metrics:
                    found_metrics.add(canonical_metric)
                    facts.metric_mentions.append(canonical_metric)
                    start = max(0, match.start() - 60)
                    end = min(len(text), match.end() + 60)
                    evidence_list.append(
                        DocumentEvidence(
                            text_snippet=text[start:end].replace("\n", " ").strip(),
                            source_file=filename,
                            page_number=page,
                            confidence=0.95,
                        )
                    )

        # 2. Target Variable Hints
        found_targets = set()
        for pattern in TARGET_PATTERNS:
            for text, page in chunks:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    candidate = match.group(1).strip()
                    # Filter out common stop words
                    if candidate.lower() not in ["the", "this", "each", "a", "an", "all", "which", "our"] and candidate not in found_targets:
                        found_targets.add(candidate)
                        facts.target_variable_mentions.append(candidate)
                        start = max(0, match.start() - 40)
                        end = min(len(text), match.end() + 40)
                        evidence_list.append(
                            DocumentEvidence(
                                text_snippet=text[start:end].replace("\n", " ").strip(),
                                source_file=filename,
                                page_number=page,
                                confidence=0.85,
                            )
                        )

        # 3. ID Column Hints
        found_ids = set()
        for pattern in ID_PATTERNS:
            for text, page in chunks:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    candidate = match.group(1).strip()
                    if candidate not in found_ids:
                        found_ids.add(candidate)
                        facts.id_column_mentions.append(candidate)
                        start = max(0, match.start() - 40)
                        end = min(len(text), match.end() + 40)
                        evidence_list.append(
                            DocumentEvidence(
                                text_snippet=text[start:end].replace("\n", " ").strip(),
                                source_file=filename,
                                page_number=page,
                                confidence=0.85,
                            )
                        )

        # 4. Rules & Constraints
        for pattern in RULE_PATTERNS:
            for text, page in chunks:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    rule_snippet = match.group(1).strip()
                    facts.constraints_and_rules.append(rule_snippet)

        facts.evidence_snippets = evidence_list
        logger.info(
            "Document '%s' analyzed: %d metric mentions, %d target hints, %d evidence snippets.",
            filename,
            len(facts.metric_mentions),
            len(facts.target_variable_mentions),
            len(evidence_list),
        )
        return facts

    @classmethod
    def consolidate_document_facts(cls, file_paths: List[Path]) -> ExtractedDocumentFacts:
        """Consolidate facts from multiple competition documentation files."""
        consolidated = ExtractedDocumentFacts()
        for path in file_paths:
            if not path.exists():
                continue
            facts = cls.extract_from_file(path)
            consolidated.metric_mentions.extend([m for m in facts.metric_mentions if m not in consolidated.metric_mentions])
            consolidated.target_variable_mentions.extend([t for t in facts.target_variable_mentions if t not in consolidated.target_variable_mentions])
            consolidated.id_column_mentions.extend([i for i in facts.id_column_mentions if i not in consolidated.id_column_mentions])
            consolidated.constraints_and_rules.extend(facts.constraints_and_rules)
            consolidated.evidence_snippets.extend(facts.evidence_snippets)
            consolidated.full_text_length += facts.full_text_length

        return consolidated


document_rules_extractor = DocumentRulesExtractor()
