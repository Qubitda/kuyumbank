"""F7-023 — CRM sync port (opt-in; no-op/fake)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class CRMSyncRequest:
    firma_id: int
    event: str
    payload: dict[str, Any]


@dataclass(frozen=True)
class CRMSyncResult:
    ok: bool
    skipped: bool = False
    detail: str = ""


class CRMPort(Protocol):
    def sync(self, req: CRMSyncRequest) -> CRMSyncResult: ...
