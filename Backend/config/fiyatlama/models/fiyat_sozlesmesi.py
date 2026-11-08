from django.conf import settings
from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import DateRangeField, RangeOperators
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Func, Q, Value
from django.db.models.functions import Coalesce


class DateRange(Func):
    """daterange(baslangic, bitis, '[]') — ADR-0007 §2.3."""

    function = "DATERANGE"
    output_field = DateRangeField()


class FiyatSozlesmesi(models.Model):
    """
    Firma bazlı fiyat sözleşmesi.

    - AKTIF sonrası kalem/tarih değişmez; yeni versiyon açılır (ADR-0007 §2.3).
    - Aynı firma+tip+kanal anahtarında AKTIF tarih aralıkları çakışmaz (K-008).
    """

    class KontratTipi(models.TextChoices):
        TEDARIKCI = "TEDARIKCI", "Tedarikçi (işçilik)"
        ALICI = "ALICI", "Alıcı (servis bedeli)"

    class Durum(models.TextChoices):
        TASLAK = "TASLAK", "Taslak"
        AKTIF = "AKTIF", "Aktif"
        PASIF = "PASIF", "Pasif"
        SURESI_DOLDU = "SURESI_DOLDU", "Süresi doldu"

    firma = models.ForeignKey(
        "firmalar.Firma",
        on_delete=models.PROTECT,
        related_name="fiyat_sozlesmeleri",
    )
    kontrat_tipi = models.CharField(max_length=16, choices=KontratTipi.choices)
    satis_kanali = models.ForeignKey(
        "tanimlar.SatisKanali",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="fiyat_sozlesmeleri",
        help_text="Boş = tüm kanallar (fallback).",
    )
    gecerlilik_baslangic = models.DateField()
    gecerlilik_bitis = models.DateField()
    durum = models.CharField(
        max_length=16, choices=Durum.choices, default=Durum.TASLAK
    )
    olusturan_kullanici = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="olusturdugu_sozlesmeler",
    )
    onaylayan_kullanici = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="onayladigi_sozlesmeler",
    )
    versiyon = models.PositiveIntegerField(default=1)
    onceki_versiyon = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="sonraki_versiyonlar",
    )
    notlar = models.TextField(blank=True)
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    guncelleme_tarihi = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Fiyat Sözleşmesi"
        verbose_name_plural = "Fiyat Sözleşmeleri"
        ordering = ["firma", "-gecerlilik_baslangic", "-versiyon"]
        permissions = [
            ("manage_sozlesme", "Fiyat sözleşmesini yönetebilir"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    gecerlilik_bitis__gte=models.F("gecerlilik_baslangic")
                ),
                name="sozlesme_tarih_sirasi",
            ),
            models.UniqueConstraint(
                fields=["firma", "kontrat_tipi", "versiyon"],
                condition=models.Q(satis_kanali__isnull=True),
                name="sozlesme_firma_tip_versiyon_kanalsiz_uniq",
            ),
            models.UniqueConstraint(
                fields=["firma", "kontrat_tipi", "satis_kanali", "versiyon"],
                condition=models.Q(satis_kanali__isnull=False),
                name="sozlesme_firma_tip_kanal_versiyon_uniq",
            ),
            # K-008: AKTIF aralık çakışması (NULL kanal → COALESCE 0)
            ExclusionConstraint(
                name="sozlesme_aktif_tarih_cakisma",
                expressions=[
                    (F("firma"), RangeOperators.EQUAL),
                    (F("kontrat_tipi"), RangeOperators.EQUAL),
                    (
                        Coalesce(F("satis_kanali_id"), Value(0)),
                        RangeOperators.EQUAL,
                    ),
                    (
                        DateRange(
                            F("gecerlilik_baslangic"),
                            F("gecerlilik_bitis"),
                            Value("[]"),
                        ),
                        RangeOperators.OVERLAPS,
                    ),
                ],
                condition=Q(durum="AKTIF"),
            ),
        ]

    def __str__(self) -> str:
        return (
            f"{self.firma} {self.kontrat_tipi} v{self.versiyon} "
            f"({self.gecerlilik_baslangic}→{self.gecerlilik_bitis})"
        )

    def clean(self):
        super().clean()
        if self.gecerlilik_bitis and self.gecerlilik_baslangic:
            if self.gecerlilik_bitis < self.gecerlilik_baslangic:
                raise ValidationError("Bitiş tarihi başlangıçtan önce olamaz.")
        if self.onceki_versiyon_id:
            if self.onceki_versiyon.firma_id != self.firma_id:
                raise ValidationError("Önceki versiyon farklı firmaya ait.")
            if self.onceki_versiyon.kontrat_tipi != self.kontrat_tipi:
                raise ValidationError("Önceki versiyon farklı kontrat tipinde.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
