"""Ürün durum geçişleri: kurallar tek yerde durur.

Admin, ileride tedarikçi paneli ve API aynı fonksiyonları çağırır (Medusa'daki
"workflow" katmanının karşılığı). Hiçbir yer onay_durumu / yayin_durumu alanını
doğrudan yazmamalı.
"""
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import Urun


def platform_kullanicisi_mi(kullanici):
    return bool(kullanici.is_superuser or (kullanici.firma_id and kullanici.firma.platform_mu))


def _platform_sart(kullanici):
    if not platform_kullanicisi_mi(kullanici):
        raise ValidationError("Bu işlem yalnızca platform kullanıcılarının yetkisindedir.")


def _kilitle(urun):
    """Aynı ürün üzerinde eşzamanlı geçişleri sıraya sokar ve güncel hâli döndürür."""
    return Urun.objects.select_for_update().get(pk=urun.pk)


def _gonderime_hazir_mi(urun):
    varyantlar = list(urun.varyantlar.filter(aktif=True))
    if not varyantlar:
        raise ValidationError("En az bir aktif varyant girilmeden onaya gönderilemez.")
    for v in varyantlar:
        try:
            v.full_clean()
        except ValidationError as e:
            raise ValidationError(f"Varyant {v.sku or v.pk}: " + "; ".join(e.messages))


@transaction.atomic
def onaya_gonder(urun, kullanici):
    urun = _kilitle(urun)
    if urun.onay_durumu not in ("taslak", "reddedildi"):
        raise ValidationError("Yalnızca taslak veya reddedilmiş ürün onaya gönderilebilir.")
    _gonderime_hazir_mi(urun)
    urun.onay_durumu = "onay_bekliyor"
    urun.full_clean()
    urun.save(update_fields=["onay_durumu", "guncelleme_zamani"])
    return urun


@transaction.atomic
def onayla(urun, kullanici):
    _platform_sart(kullanici)
    urun = _kilitle(urun)
    if urun.onay_durumu != "onay_bekliyor":
        raise ValidationError("Yalnızca onay bekleyen ürün onaylanabilir.")
    urun.onay_durumu = "onayli"
    urun.onaylayan_kullanici = kullanici
    urun.onay_zamani = timezone.now()
    urun.red_nedeni = ""
    urun.full_clean()
    urun.save(update_fields=["onay_durumu", "onaylayan_kullanici", "onay_zamani", "red_nedeni", "guncelleme_zamani"])
    return urun


@transaction.atomic
def reddet(urun, kullanici, neden):
    _platform_sart(kullanici)
    if not (neden or "").strip():
        raise ValidationError("Red nedeni yazılmalıdır.")
    urun = _kilitle(urun)
    if urun.onay_durumu != "onay_bekliyor":
        raise ValidationError("Yalnızca onay bekleyen ürün reddedilebilir.")
    urun.onay_durumu = "reddedildi"
    urun.red_nedeni = neden.strip()
    urun.yayin_durumu = "pasif"
    urun.onaylayan_kullanici = None
    urun.onay_zamani = None
    urun.full_clean()
    urun.save(update_fields=[
        "onay_durumu", "red_nedeni", "yayin_durumu", "onaylayan_kullanici", "onay_zamani", "guncelleme_zamani",
    ])
    return urun


@transaction.atomic
def yayina_al(urun, kullanici, durum="aktif"):
    _platform_sart(kullanici)
    if durum not in ("aktif", "yakinda"):
        raise ValidationError("Yayın durumu 'aktif' veya 'yakinda' olmalıdır.")
    urun = _kilitle(urun)
    if urun.onay_durumu != "onayli":
        raise ValidationError("Yalnızca onaylı ürün yayına alınabilir.")
    if durum == "aktif" and not urun.kanallar.filter(aktif=True).exists():
        raise ValidationError("Aktif yayın için ürünün en az bir satış kanalı seçili olmalıdır.")
    urun.yayin_durumu = durum
    urun.full_clean()
    urun.save(update_fields=["yayin_durumu", "guncelleme_zamani"])
    return urun


@transaction.atomic
def pasife_al(urun, kullanici):
    _platform_sart(kullanici)
    urun = _kilitle(urun)
    urun.yayin_durumu = "pasif"
    urun.save(update_fields=["yayin_durumu", "guncelleme_zamani"])
    return urun
