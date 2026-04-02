from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class EvidenceSuggestion:
    label: str
    reason: str


@dataclass(frozen=True)
class NextStep:
    label: str
    detail: str


class CaseAssistantService(ABC):
    """Abstract interface for the NULLA assistant seam."""

    @abstractmethod
    def suggest_missing_evidence(self, workspace_id: int, case_id: int) -> Iterable[EvidenceSuggestion]:
        """Return evidence types NULLA suggests collecting."""

    @abstractmethod
    def summarize_timeline_draft(self, workspace_id: int, case_id: int) -> str:
        """Generate a draft summary of the case timeline."""

    @abstractmethod
    def propose_next_steps(self, workspace_id: int, case_id: int) -> Iterable[NextStep]:
        """Propose deterministic next steps for workflow triage."""

    @abstractmethod
    def classify_evidence_source(self, workspace_id: int, case_id: int, evidence_id: int) -> str:
        """Return a classification label for the provided evidence item."""


class NoopCaseAssistantService(CaseAssistantService):
    """Default no-op assistant until NULLA integration ships."""

    def suggest_missing_evidence(self, workspace_id: int, case_id: int) -> Iterable[EvidenceSuggestion]:
        return ()

    def summarize_timeline_draft(self, workspace_id: int, case_id: int) -> str:
        return ""

    def propose_next_steps(self, workspace_id: int, case_id: int) -> Iterable[NextStep]:
        return ()

    def classify_evidence_source(self, workspace_id: int, case_id: int, evidence_id: int) -> str:
        return "unclassified"
