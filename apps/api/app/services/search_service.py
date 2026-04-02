from __future__ import annotations

import json
from typing import Callable, Sequence

from sqlmodel import Session, select

from app.models.claim import Case, EvidenceItem, TimelineEvent
from app.schemas.search import SearchResultRead


class SearchService:
    _max_results = 50

    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    def search(self, workspace_id: int, query: str, case_id: int | None = None) -> list[SearchResultRead]:
        normalized = query.strip()
        if not normalized:
            return []
        term = normalized.lower()
        results: list[SearchResultRead] = []
        with self._session_factory() as session:
            results.extend(self._search_cases(session, workspace_id, case_id, term))
            results.extend(self._search_timeline(session, workspace_id, case_id, term))
            results.extend(self._search_evidence(session, workspace_id, case_id, term))
        results.sort(key=lambda hit: (-hit.score, hit.case_title))
        return results[: self._max_results]

    def _search_cases(
        self,
        session: Session,
        workspace_id: int,
        case_id: int | None,
        term: str,
    ) -> list[SearchResultRead]:
        stmt = select(Case).where(Case.workspace_id == workspace_id)
        if case_id:
            stmt = stmt.where(Case.id == case_id)
        hits: list[SearchResultRead] = []
        for entry in session.exec(stmt).all():
            score = 0
            match_field = ""
            snippet = ""
            for field_name, weight, value in self._case_fields(entry):
                if not value:
                    continue
                lowered = value.lower()
                if term in lowered:
                    score += weight
                    if not snippet:
                        snippet = self._make_snippet(value, term)
                    if not match_field:
                        match_field = field_name
            if score:
                hits.append(
                    SearchResultRead(
                        case_id=entry.id,
                        case_title=entry.title,
                        source_type="case",
                        source_id=entry.id,
                        match_field=match_field or "case",
                        snippet=snippet or entry.title,
                        score=score,
                        details={"field": match_field or "case"},
                    )
                )
        return hits

    def _search_timeline(
        self,
        session: Session,
        workspace_id: int,
        case_id: int | None,
        term: str,
    ) -> list[SearchResultRead]:
        stmt = (
            select(TimelineEvent)
            .join(Case, TimelineEvent.case_id == Case.id)
            .where(Case.workspace_id == workspace_id)
        )
        if case_id:
            stmt = stmt.where(TimelineEvent.case_id == case_id)
        hits: list[SearchResultRead] = []
        for event in session.exec(stmt).all():
            body = event.body or ""
            if term not in body.lower():
                continue
            hits.append(
                SearchResultRead(
                    case_id=event.case_id,
                    case_title=self._get_case_title(event.case_id, session),
                    source_type="timeline",
                    source_id=event.id,
                    match_field="timeline",
                    snippet=self._make_snippet(body, term),
                    score=3,
                    details={"event_type": event.event_type},
                )
            )
        return hits

    def _search_evidence(
        self,
        session: Session,
        workspace_id: int,
        case_id: int | None,
        term: str,
    ) -> list[SearchResultRead]:
        stmt = (
            select(EvidenceItem)
            .join(Case, EvidenceItem.case_id == Case.id)
            .where(Case.workspace_id == workspace_id)
        )
        if case_id:
            stmt = stmt.where(EvidenceItem.case_id == case_id)
        hits: list[SearchResultRead] = []
        for item in session.exec(stmt).all():
            score = 0
            match_field = ""
            snippet = ""
            extracted = item.extracted_text or ""
            if extracted and term in extracted.lower():
                score += 4
                snippet = snippet or self._make_snippet(extracted, term)
                match_field = match_field or "extracted_text"
            if item.source_label and term in item.source_label.lower():
                score += 1
                if not snippet:
                    snippet = self._make_snippet(item.source_label, term)
                match_field = match_field or "source_label"
            metadata = json.dumps(item.metadata_json or {}, ensure_ascii=False)
            if metadata and term in metadata.lower():
                score += 2
                if not snippet:
                    snippet = self._make_snippet(metadata, term)
                match_field = match_field or "metadata"
            if score:
                hits.append(
                    SearchResultRead(
                        case_id=item.case_id,
                        case_title=self._get_case_title(item.case_id, session),
                        source_type="evidence",
                        source_id=item.id,
                        match_field=match_field or "evidence",
                        snippet=snippet or (item.source_label or item.original_filename),
                        score=score,
                        details={
                            "kind": getattr(item.kind, "value", item.kind),
                            "filename": item.original_filename,
                        },
                    )
                )
        return hits

    def _case_fields(self, entry: Case) -> Sequence[tuple[str, int, str | None]]:
        return [
            ("title", 5, entry.title),
            ("summary", 3, entry.summary),
            ("order_reference", 2, entry.order_reference),
            ("counterparty", 2, entry.counterparty_name),
        ]

    def _make_snippet(self, text: str, term: str, context: int = 80) -> str:
        snippet = text.strip()
        lowered = snippet.lower()
        idx = lowered.find(term)
        if idx == -1:
            return snippet[:context] + ("..." if len(snippet) > context else "")
        start = max(0, idx - 40)
        end = min(len(snippet), idx + len(term) + 40)
        fragment = snippet[start:end].strip()
        if start > 0:
            fragment = f"...{fragment}"
        if end < len(snippet):
            fragment = f"{fragment}..."
        return fragment

    def _get_case_title(self, case_id: int, session: Session) -> str:
        case = session.get(Case, case_id)
        return case.title if case else "Unknown case"
