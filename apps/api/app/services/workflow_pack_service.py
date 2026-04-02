from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from app.models.claim import Case, ClaimType
from app.schemas.readiness import ReadinessReport
from app.workflow.packs import WorkflowPack, get_pack


@dataclass(frozen=True)
class WorkflowTask:
    key: str
    title: str
    description: str
    priority: int
    status: str


class WorkflowPackService:
    def __init__(self, pack_provider: Callable[[ClaimType], WorkflowPack | None] = get_pack) -> None:
        self._pack_provider = pack_provider

    def describe(self, case: Case, readiness: ReadinessReport) -> tuple[WorkflowPack | None, list[WorkflowTask]]:
        pack = self._pack_provider(case.claim_type)
        if not pack:
            return None, []
        missing_keys = {check.rule_key for check in readiness.checks if not check.satisfied}
        tasks: list[WorkflowTask] = []
        for definition in pack.tasks:
            status = "open" if definition.key in missing_keys else "complete"
            tasks.append(
                WorkflowTask(
                    key=definition.key,
                    title=definition.title,
                    description=definition.description,
                    priority=definition.priority,
                    status=status,
                )
            )
        return pack, tasks
