"""
Verilen firma + kontrat tipi + tarih + metal + ayar için geçerli kalemi seçer.

Öncelik (ADR-0007 §2.2 / görev dilim 3.2):
1. Kanal eşleşmesi (spesifik > kanalsız fallback)
2. Ayar eşleşmesi (spesifik > genel)
3. Yüksek versiyon
4. Eşit skor → hata; fiyat yok
"""

from datetime import date

from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.db.models import Q

from fiyatlama.models import FiyatSozlesmesi, FiyatSozlesmesiKalemi


class SozlesmeYokHatasi(ObjectDoesNotExist):
    pass


class CokluSozlesmeHatasi(MultipleObjectsReturned):
    pass


def _ayar_or_none(ayar):
    """Spesifik ayar VEYA None (tüm ayarlar)."""
    return Q(ayar=ayar) | Q(ayar__isnull=True)


def cozumle(
    *,
    firma,
    kontrat_tipi: str,
    tarih: date,
    metal=None,
    ayar=None,
    satis_kanali=None,
) -> FiyatSozlesmesiKalemi:
    qs = FiyatSozlesmesi.objects.filter(
        firma=firma,
        kontrat_tipi=kontrat_tipi,
        durum=FiyatSozlesmesi.Durum.AKTIF,
        gecerlilik_baslangic__lte=tarih,
        gecerlilik_bitis__gte=tarih,
    ).select_related("satis_kanali")

    # Kanallı baskın; kanalsız diğer kanallara fallback (ADR-0007 §2.3 matris)
    kanal_specific = qs.filter(satis_kanali=satis_kanali) if satis_kanali else qs.none()
    kanal_general = qs.filter(satis_kanali__isnull=True)
    aday_sozlesmeler = list(kanal_specific) + list(kanal_general)

    if not aday_sozlesmeler:
        raise SozlesmeYokHatasi(
            f"{firma} / {kontrat_tipi} / {tarih} için sözleşme yok."
        )

    sozlesme_ids = [s.id for s in aday_sozlesmeler]

    kalem_qs = FiyatSozlesmesiKalemi.objects.filter(
        sozlesme_id__in=sozlesme_ids, metal=metal
    ).select_related("sozlesme")
    if ayar is not None:
        kalem_qs = kalem_qs.filter(_ayar_or_none(ayar))
    else:
        kalem_qs = kalem_qs.filter(ayar__isnull=True)

    kalemler = list(kalem_qs)

    if not kalemler:
        raise SozlesmeYokHatasi(
            f"{firma} / {kontrat_tipi} / metal={metal} / ayar={ayar} için kalem yok."
        )

    kanal_id = satis_kanali.id if satis_kanali else None

    def _skor(k):
        return (
            1 if (kanal_id is not None and k.sozlesme.satis_kanali_id == kanal_id) else 0,
            1 if k.ayar_id is not None else 0,
            k.sozlesme.versiyon,
        )

    kalemler.sort(key=_skor, reverse=True)

    if len(kalemler) > 1 and _skor(kalemler[0]) == _skor(kalemler[1]):
        raise CokluSozlesmeHatasi(
            f"{firma} / {kontrat_tipi} / {tarih} için birden fazla eşdeğer kalem: "
            f"{[k.id for k in kalemler]}"
        )

    return kalemler[0]
