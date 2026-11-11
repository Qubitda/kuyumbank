"""Django system checks — prod operasyonel güvenlik."""

from __future__ import annotations

import sys

from django.conf import settings
from django.core.checks import Error, Warning, register


def _running_tests() -> bool:
    return any(a == "test" or a.startswith("test") for a in sys.argv)


@register()
def check_shared_cache_for_throttle(app_configs, **kwargs):
    """DEBUG=False: LocMem yasak (ALLOW_LOCMEM_CACHE yoksa Error)."""
    if getattr(settings, "DEBUG", False) or _running_tests():
        return []
    caches = getattr(settings, "CACHES", {}) or {}
    default = caches.get("default") or {}
    backend = str(default.get("BACKEND") or "")
    if "locmem" not in backend.lower():
        return []
    if getattr(settings, "ALLOW_LOCMEM_CACHE", False):
        return [
            Warning(
                "ALLOW_LOCMEM_CACHE=1: LocMem prod'da bilerek açık "
                "(throttle limitleri worker başına).",
                id="kuyumbank.W001",
            )
        ]
    return [
        Error(
            "CACHES default LocMemCache prod'da yasak. "
            "DatabaseCache/Redis kullanın veya ALLOW_LOCMEM_CACHE=1.",
            id="kuyumbank.E001",
        )
    ]


@register()
def check_fake_providers_in_prod(app_configs, **kwargs):
    if getattr(settings, "DEBUG", False) or _running_tests():
        return []
    if getattr(settings, "ALLOW_FAKE_PROVIDERS", False):
        return [
            Warning(
                "ALLOW_FAKE_PROVIDERS=1: fake ödeme/kargo prod'da açık.",
                id="kuyumbank.W002",
            )
        ]
    errors = []
    if (getattr(settings, "PAYMENT_PROVIDER", "") or "").lower() == "fake":
        errors.append(
            Error(
                "PAYMENT_PROVIDER=fake prod'da yasak. Gerçek adaptör veya "
                "ALLOW_FAKE_PROVIDERS=1.",
                id="kuyumbank.E002",
            )
        )
    if (getattr(settings, "CARRIER_PROVIDER", "") or "").lower() == "fake":
        errors.append(
            Error(
                "CARRIER_PROVIDER=fake prod'da yasak. Gerçek adaptör veya "
                "ALLOW_FAKE_PROVIDERS=1.",
                id="kuyumbank.E003",
            )
        )
    return errors


@register()
def check_mfa_enforce_in_prod(app_configs, **kwargs):
    if getattr(settings, "DEBUG", False) or _running_tests():
        return []
    if getattr(settings, "MFA_ENFORCE_PLATFORM", False):
        return []
    return [
        Warning(
            "MFA_ENFORCE_PLATFORM=False: platform/act-as e-posta OTP kapalı.",
            id="kuyumbank.W003",
        )
    ]
