"""F5-030 — Alıcı finans özeti (maskeli); komisyon/marj/tedarikçi yok."""

from __future__ import annotations

from django.core.exceptions import PermissionDenied

from finans.models import PaymentIntent
from finans.services import credit_servisi


# Yanıttan yasak anahtarlar (kör havuz + gizlilik)
FORBIDDEN_KEYS = frozenset(
    {
        "komisyon",
        "marj",
        "margin",
        "commission",
        "tedarikci",
        "tedarikci_id",
        "karsi_firma",
        "karsi_firma_id",
        "ledger_entry",
        "ledger_entry_id",
        "maliyet",
        "cost",
    }
)


def present_payment_intent_masked(pi: PaymentIntent) -> dict:
    return {
        "id": pi.pk,
        "order_id": pi.order_id,
        "durum": pi.durum,
        "tutar": str(pi.tutar),
        "para_birimi": pi.para_birimi,
        "olusturma_tarihi": (
            pi.olusturma_tarihi.isoformat() if pi.olusturma_tarihi else None
        ),
    }


def ozet_for_actor(*, actor, para_birimi: str = "TRY", intent_limit: int = 10) -> dict:
    """Alıcıya finans paneli DTO — credit + son payment intent’ler."""
    firma = credit_servisi.require_buyer_firma(actor)
    pb = (para_birimi or "TRY").strip().upper()
    credit = credit_servisi.present_credit(
        credit_servisi.ozet_for_actor(actor=actor, para_birimi=pb)
    )
    intents = (
        PaymentIntent.objects.filter(alici_firma=firma)
        .order_by("-olusturma_tarihi", "-pk")[: max(1, min(intent_limit, 50))]
    )
    data = {
        "para_birimi": pb,
        "credit": credit,
        "payment_intents": [present_payment_intent_masked(pi) for pi in intents],
    }
    assert_masked(data)
    return data


def assert_masked(data: dict) -> None:
    """Kör alan assert — test ve sunum sözleşmesi."""
    stack = [data]
    while stack:
        cur = stack.pop()
        if isinstance(cur, dict):
            for k, v in cur.items():
                if k.lower() in FORBIDDEN_KEYS or k in FORBIDDEN_KEYS:
                    raise PermissionDenied(f"Maske ihlali: alan {k!r}")
                stack.append(v)
        elif isinstance(cur, list):
            stack.extend(cur)
