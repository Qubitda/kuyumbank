"""F8-006 — Kritik yol süre ölçümü (quote / lock / cart+checkout).

Baseline: management command çıktısı; soft eşik flake önlemek için geniş.
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass
from decimal import Decimal
from typing import Callable

# Soft üst sınır (saniye) — CI/ortam farkı için geniş; sıkı SLA değil.
DEFAULT_SOFT_LIMIT_S = 30.0


@dataclass(frozen=True)
class PerfSample:
    name: str
    elapsed_ms: float
    ok: bool
    detail: str = ""


def _time_call(name: str, fn: Callable[[], None], *, soft_limit_s: float) -> PerfSample:
    t0 = time.perf_counter()
    try:
        fn()
        elapsed = (time.perf_counter() - t0) * 1000.0
        ok = (elapsed / 1000.0) <= soft_limit_s
        return PerfSample(name=name, elapsed_ms=round(elapsed, 3), ok=ok)
    except Exception as exc:  # noqa: BLE001 — smoke raporu
        elapsed = (time.perf_counter() - t0) * 1000.0
        return PerfSample(
            name=name,
            elapsed_ms=round(elapsed, 3),
            ok=False,
            detail=str(exc)[:200],
        )


def run_quote_lock_checkout_smoke(
    *,
    alici_firma,
    satis_kanali,
    varyant,
    quote_actor,
    buyer,
    soft_limit_s: float = DEFAULT_SOFT_LIMIT_S,
) -> list[PerfSample]:
    """Mevcut dünya üzerinde quote → lock → cart line → checkout süreleri."""
    from fiyatlama.services import pricing_service
    from siparis.services import cart_servisi, checkout_servisi

    samples: list[PerfSample] = []
    quote_box: dict = {}

    def do_quote():
        quote_box["q"] = pricing_service.quote(
            alici_firma=alici_firma,
            satis_kanali=satis_kanali,
            varyant=varyant,
            kullanici=quote_actor,
        )

    samples.append(_time_call("quote", do_quote, soft_limit_s=soft_limit_s))

    def do_lock():
        quote_box["lock"] = pricing_service.lock_quote(
            quote_box["q"], kullanici=buyer
        )

    if samples[-1].ok and "q" in quote_box:
        samples.append(_time_call("lock_quote", do_lock, soft_limit_s=soft_limit_s))
    else:
        samples.append(
            PerfSample(name="lock_quote", elapsed_ms=0.0, ok=False, detail="quote failed")
        )

    def do_cart_checkout():
        # Yeni quote — lock zaten quote'u tüketti olabilir; taze quote
        q2 = pricing_service.quote(
            alici_firma=alici_firma,
            satis_kanali=satis_kanali,
            varyant=varyant,
            kullanici=quote_actor,
        )
        cart_servisi.satir_ekle(actor=buyer, price_quote=q2, miktar=Decimal("1"))
        checkout_servisi.checkout(
            actor=buyer, idempotency_key=f"perf-smoke-{int(time.time() * 1000)}"
        )

    samples.append(
        _time_call("cart_checkout", do_cart_checkout, soft_limit_s=soft_limit_s)
    )
    return samples


def samples_to_rows(samples: list[PerfSample]) -> list[dict]:
    return [asdict(s) for s in samples]
