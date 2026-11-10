"""CAP-PIYASA / ADR-0018 — fiyat kaynağı ve feed_health sabitleri."""

from __future__ import annotations


class FiyatKaynagi:
    CANLI_PIYASA = "CANLI_PIYASA"
    MANUEL_GIRIS = "MANUEL_GIRIS"
    MIRAS = "MIRAS"  # yalnız ürün + ayar

    CHOICES_POLITIKA = [
        (CANLI_PIYASA, "Canlı piyasa"),
        (MANUEL_GIRIS, "Manuel giriş"),
    ]
    CHOICES_KATMAN = CHOICES_POLITIKA + [(MIRAS, "Miras (üst katman)")]


class FeedHealth:
    FEED_OK = "FEED_OK"
    FEED_STALE_LKG = "FEED_STALE_LKG"
    FEED_LOCKED_MANUEL = "FEED_LOCKED_MANUEL"
    FEED_FAIL = "FEED_FAIL"

    CHOICES = [
        (FEED_OK, "OK"),
        (FEED_STALE_LKG, "Stale — LKG"),
        (FEED_LOCKED_MANUEL, "Manuel kilit"),
        (FEED_FAIL, "Fail"),
    ]


TROY_OZ_GRAM = "31.1035"  # Decimal string; float yasak
ARA_QUANT = "0.000001"
TRY_QUANT = "0.01"
