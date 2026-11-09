"""F7-022 — Tek connector kayıt defteri (payment + carrier factory)."""

from __future__ import annotations

from typing import Any, Callable


class ConnectorRegistry:
    def __init__(self) -> None:
        self._factories: dict[str, Callable[..., Any]] = {}

    def register(self, name: str, factory: Callable[..., Any]) -> None:
        key = (name or "").strip().lower()
        if not key:
            raise ValueError("connector name zorunlu")
        self._factories[key] = factory

    def get(self, name: str, **kwargs: Any) -> Any:
        key = (name or "").strip().lower()
        if key not in self._factories:
            raise KeyError(f"Bilinmeyen connector: {name!r}")
        return self._factories[key](**kwargs)

    def names(self) -> list[str]:
        return sorted(self._factories)


_REGISTRY: ConnectorRegistry | None = None


def get_registry() -> ConnectorRegistry:
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = ConnectorRegistry()
        _bootstrap(_REGISTRY)
    return _REGISTRY


def _bootstrap(reg: ConnectorRegistry) -> None:
    from finans.payments.factory import get_payment_adapter
    from lojistik.carriers.factory import get_carrier_adapter

    reg.register("payment", get_payment_adapter)
    reg.register("carrier", get_carrier_adapter)

    from integrations.erp.fake import FakeERPAdapter
    from integrations.crm.fake import FakeCRMAdapter

    reg.register("erp", lambda **kw: FakeERPAdapter(**kw))
    reg.register("crm", lambda **kw: FakeCRMAdapter(**kw))


def reset_registry_for_tests() -> None:
    global _REGISTRY
    _REGISTRY = None
