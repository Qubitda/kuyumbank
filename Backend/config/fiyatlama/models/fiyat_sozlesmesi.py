from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class FiyatSozlesmesi(models.Model):
    """
    Firma bazlı fiyat sözleşmesi.

    - Sözleşme bir firmanın belirli bir dönem için geçerli marj/işçilik
      kurallarını taşır. Aynı firma için farklı dönemler ayrı sözleşmelerdir.
    - Şartlar değişince ESKİ SÖZLEŞME DEĞİŞTİRİLMEZ; yeni bir versiyon
      (onceki_versiyon=eski) açılır.
    - `kontrat_tipi` alıcı tarafı mı tedarikçi tarafı mı olduğunu belirler.
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
        help_text="Boş = tüm kanallar.",
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
            # Kanalsız (satis_kanali IS NULL): firma+tip+versiyon tekil
            models.UniqueConstraint(
                fields=["firma", "kontrat_tipi", "versiyon"],
                condition=models.Q(satis_kanali__isnull=True),
                name="sozlesme_firma_tip_versiyon_kanalsiz_uniq",
            ),
            # Kanallı (satis_kanali IS NOT NULL): firma+tip+kanal+versiyon tekil
            models.UniqueConstraint(
                fields=["firma", "kontrat_tipi", "satis_kanali", "versiyon"],
                condition=models.Q(satis_kanali__isnull=False),
                name="sozlesme_firma_tip_kanal_versiyon_uniq",
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