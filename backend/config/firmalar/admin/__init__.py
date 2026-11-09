"""Admin kayıtlarını alt modüllerden yükler."""

from .firma_admin import FirmaAdmin, FirmaAdresiAdmin, FirmaBankaHesabiAdmin, FirmaAdresiInline, FirmaBankaHesabiInline
from .kullanici_admin import KullaniciAdmin
from . import org_admin  # noqa: F401 — OrgBirimi/OrgUyeligi register
