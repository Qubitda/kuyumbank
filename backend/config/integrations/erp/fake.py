"""Fake ERP — roundtrip test (F7-021)."""

from __future__ import annotations

from integrations.erp.port import ERPSyncRequest, ERPSyncResult


class FakeERPAdapter:
    def __init__(self, *, force_fail: bool = False) -> None:
        self.force_fail = force_fail
        self.calls: list[ERPSyncRequest] = []

    def push_order(self, req: ERPSyncRequest) -> ERPSyncResult:
        self.calls.append(req)
        if self.force_fail:
            return ERPSyncResult(ok=False, external_ref="", detail="fake_fail")
        return ERPSyncResult(
            ok=True,
            external_ref=f"ERP-{req.entity_type}-{req.entity_id}",
            detail="accepted",
        )
