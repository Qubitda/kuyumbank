"""Kanonik iş rolleri — tek kaynak (ADR-0003-01, ADR-0004).

Rol kodları string literal olarak app geneline dağılmaz; buradan import edilir.
"""

PLATFORM_FIRMA_KODU = "PLATFORM"

PLATFORM_SUPER = "platform_super"
PLATFORM_ADMIN = "platform_admin"
PLATFORM_OPS = "platform_ops"
PLATFORM_FINANCE = "platform_finance"
PLATFORM_CATALOG = "platform_catalog"
PLATFORM_QUALITY = "platform_quality"
PLATFORM_LOGISTICS = "platform_logistics"
PLATFORM_SUPPORT = "platform_support"

ALICI_YONETICI = "alici_yonetici"
ALICI_SATINALMACI = "alici_satinalmaci"
ALICI_ONAYLAYICI = "alici_onaylayici"
ALICI_FINANS = "alici_finans"
ALICI_DENETCI = "alici_denetci"

TEDARIKCI_SAHIP = "tedarikci_sahip"
TEDARIKCI_YONETICI = "tedarikci_yonetici"
TEDARIKCI_SATIS = "tedarikci_satis"
TEDARIKCI_DEPO = "tedarikci_depo"
TEDARIKCI_FINANS = "tedarikci_finans"

ROLE_CHOICES = [
    (PLATFORM_SUPER, "Platform: Super"),
    (PLATFORM_ADMIN, "Platform: Admin"),
    (PLATFORM_OPS, "Platform: Ops"),
    (PLATFORM_FINANCE, "Platform: Finans"),
    (PLATFORM_CATALOG, "Platform: Katalog"),
    (PLATFORM_QUALITY, "Platform: Kalite"),
    (PLATFORM_LOGISTICS, "Platform: Lojistik"),
    (PLATFORM_SUPPORT, "Platform: Destek"),
    (ALICI_YONETICI, "Alıcı: Yönetici"),
    (ALICI_SATINALMACI, "Alıcı: Satın almacı"),
    (ALICI_ONAYLAYICI, "Alıcı: Sipariş onaylayıcı"),
    (ALICI_FINANS, "Alıcı: Finans"),
    (ALICI_DENETCI, "Alıcı: Salt okunur denetçi"),
    (TEDARIKCI_SAHIP, "Tedarikçi: Sahip"),
    (TEDARIKCI_YONETICI, "Tedarikçi: Yönetici"),
    (TEDARIKCI_SATIS, "Tedarikçi: Satış temsilcisi"),
    (TEDARIKCI_DEPO, "Tedarikçi: Depo/sevkiyat"),
    (TEDARIKCI_FINANS, "Tedarikçi: Finans"),
]

PLATFORM_ROLLERI = frozenset({
    PLATFORM_SUPER,
    PLATFORM_ADMIN,
    PLATFORM_OPS,
    PLATFORM_FINANCE,
    PLATFORM_CATALOG,
    PLATFORM_QUALITY,
    PLATFORM_LOGISTICS,
    PLATFORM_SUPPORT,
})

ALICI_ROLLERI = frozenset({
    ALICI_YONETICI,
    ALICI_SATINALMACI,
    ALICI_ONAYLAYICI,
    ALICI_FINANS,
    ALICI_DENETCI,
})

TEDARIKCI_ROLLERI = frozenset({
    TEDARIKCI_SAHIP,
    TEDARIKCI_YONETICI,
    TEDARIKCI_SATIS,
    TEDARIKCI_DEPO,
    TEDARIKCI_FINANS,
})

ALL_ROLES = frozenset(code for code, _ in ROLE_CHOICES)

ROLE_GROUP_PREFIX = "rol:"


def role_group_name(role: str) -> str:
    return f"{ROLE_GROUP_PREFIX}{role}"
