"""F7-021 — ERP adapter portu (canlı SAP yok)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class ERPSyncRequest:
    entity_type: str
    entity_id: str
    payload: dict[str, Any]


@dataclass(frozen=True)
class ERPSyncResult:
    ok: bool
    external_ref: str
    detail: str = ""


class ERPPort(Protocol):
    def push_order(self, req: ERPSyncRequest) -> ERPSyncResult: ...
