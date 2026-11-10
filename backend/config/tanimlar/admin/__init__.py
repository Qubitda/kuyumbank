"""Tanım admin kayıtlarını alt modüllerden yükler."""

from .metal_admin import AyarMilyemAdmin, AyarMilyemInline, KiymetliMetalAdmin
from .kur_admin import (
    DovizKuruAdmin,
    KurAdminTaban,
    KurAlertKuraliAdmin,
    KurPolitikasiAdmin,
    KurSaglayiciAdmin,
    MetalKuruAdmin,
)
from .tanim_admin import FiyatGrubuAdmin, SatisKanaliAdmin
