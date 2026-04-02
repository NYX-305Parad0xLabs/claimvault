from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class EvidenceStorage(ABC):
    @abstractmethod
    def store(self, workspace_id: int, case_id: int, filename: str, content: bytes) -> str:
        """Store binary evidence and return the storage key (relative path)."""

    @abstractmethod
    def path_for(self, storage_key: str) -> Path:
        """Return the absolute file path associated with a storage key."""
