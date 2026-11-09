"""Fake / no-op CRM (F7-023)."""

from __future__ import annotations

from django.conf import settings

from integrations.crm.port import CRMSyncRequest, CRMSyncResult


class FakeCRMAdapter:
    def __init__(self, *, enabled: bool | None = None) -> None:
        if enabled is None:
            enabled = bool(getattr(settings, "CRM_SYNC_ENABLED", False))
        self.enabled = enabled
        self.calls: list[CRMSyncRequest] = []

    def sync(self, req: CRMSyncRequest) -> CRMSyncResult:
        self.calls.append(req)
        if not self.enabled:
            return CRMSyncResult(ok=True, skipped=True, detail="opt_in_off")
        return CRMSyncResult(ok=True, skipped=False, detail="fake_synced")
