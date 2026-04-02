from __future__ import annotations

import re
from pathlib import Path
from uuid import uuid4

from app.storage.base import EvidenceStorage


def _sanitize_filename(filename: str) -> str:
    name = Path(filename).name
    name = name.strip()
    if not name:
        name = uuid4().hex
    cleaned = re.sub(r"[^A-Za-z0-9_.-]", "_", name)
    return cleaned or uuid4().hex


def _resolve_unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    new_name = f"{stem}-{uuid4().hex[:8]}{suffix}"
    return path.with_name(new_name)


class LocalEvidenceStorage(EvidenceStorage):
    def __init__(self, root: Path) -> None:
        self._root = root
        self._root.mkdir(parents=True, exist_ok=True)

    def store(self, workspace_id: int, case_id: int, filename: str, content: bytes) -> str:
        workspace_dir = self._root / f"workspace_{workspace_id}" / f"case_{case_id}"
        workspace_dir.mkdir(parents=True, exist_ok=True)

        safe_name = _sanitize_filename(filename)
        target = workspace_dir / safe_name
        target = _resolve_unique_path(target)

        target.write_bytes(content)
        relative = target.relative_to(self._root)
        return str(relative)

    def path_for(self, storage_key: str) -> Path:
        target = self._root / storage_key
        if not target.exists():
            raise FileNotFoundError(storage_key)
        return target
