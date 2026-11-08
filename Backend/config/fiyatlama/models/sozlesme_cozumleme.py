"""
Verilen firma + kontrat tipi + tarih + metal + ayar için geçerli kalemi seçer.

Sıra:
1. Tarihe uyan AKTIF sözleşmeler
2. Kalem düzeyinde ayar eşleşmesi (spesifik > None)
3. Kanal önceliği (spesifik > None)
4. Versiyon (yüksek > düşük)
5. Aynı skorda iki kural varsa hata
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
    # 1) Tarihe uyan aktif sözleşmeler
    qs = FiyatSozlesmesi.objects.filter(
        firma=firma,
        kontrat_tipi=kontrat_tipi,
        durum=FiyatSozlesmesi.Durum.AKTIF,
        gecerlilik_baslangic__lte=tarih,
        gecerlilik_bitis__gte=tarih,
    ).select_related("satis_kanali")

    # Kanal filtresi: spesifik kanal önce, sonra None (tüm kanallar)
    kanal_specific = qs.filter(satis_kanali=satis_kanali) if satis_kanali else qs.none()
    kanal_general = qs.filter(satis_kanali__isnull=True)
    aday_sozlesmeler = list(kanal_specific) + list(kanal_general)

    if not aday_sozlesmeler:
        raise SozlesmeYokHatasi(
            f"{firma} / {kontrat_tipi} / {tarih} için sözleşme yok."
        )

    sozlesme_ids = [s.id for s in aday_sozlesmeler]

    # 2) Kalem düzeyinde ayar eşleşmesi
    kalem_qs = FiyatSozlesmesiKalemi.objects.filter(
        sozlesme_id__in=sozlesme_ids, metal=metal
    ).select_related("sozlesme")  # _skor() k.sozlesme erişimini N+1'den korur
    if ayar is not None:
        kalem_qs = kalem_qs.filter(_ayar_or_none(ayar))
    else:
        kalem_qs = kalem_qs.filter(ayar__isnull=True)

    kalemler = list(kalem_qs)

    if not kalemler:
        raise SozlesmeYokHatasi(
            f"{firma} / {kontrat_tipi} / metal={metal} / ayar={ayar} için kalem yok."
        )

    # 3) En spesifik ayar (dolu > None)
    spesifik = [k for k in kalemler if k.ayar_id is not None]
    if spesifik:
        kalemler = spesifik

    # 4) Spesifiklik skoru: (kanal-spesifik mi, versiyon)
    kanal_id = satis_kanali.id if satis_kanali else None

    def _skor(k):
        return (
            k.sozlesme.satis_kanali_id == kanal_id and kanal_id is not None,
            k.sozlesme.versiyon,
        )

    kalemler.sort(key=_skor, reverse=True)

    # 5) Aynı skorda iki kural varsa hata
    if len(kalemler) > 1 and _skor(kalemler[0]) == _skor(kalemler[1]):
        raise CokluSozlesmeHatasi(
            f"{firma} / {kontrat_tipi} / {tarih} için birden fazla eşdeğer kalem: "
            f"{[k.id for k in kalemler]}"
        )

    return kalemler[0]