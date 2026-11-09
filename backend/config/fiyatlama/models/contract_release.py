"""Contract release — sözleşmeli miktar serbest bırakma (F5-041).

Release ≠ PriceQuote: quote/lock aggregate’lerine yazılmaz.
"""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class ContractReleasePlan(models.Model):
    class Durum(models.TextChoices):
        TASLAK = "TASLAK", "Taslak"
        AKTIF = "AKTIF", "Aktif"
        KAPALI = "KAPALI", "Kapalı"

    class Birim(models.TextChoices):
        ADET = "ADET", "Adet"
        GRAM = "GRAM", "Gram"

    sozlesme = models.ForeignKey(
        "fiyatlama.FiyatSozlesmesi",
        on_delete=models.PROTECT,
        related_name="release_plans",
    )
    varyant = models.ForeignKey(
        "urunler.Varyant",
        on_delete=models.PROTECT,
        related_name="contract_release_plans",
    )
    birim = models.CharField(max_length=8, choices=Birim.choices)
    toplam_taahhut = models.DecimalField(max_digits=18, decimal_places=6)
    durum = models.CharField(
        max_length=16, choices=Durum.choices, default=Durum.TASLAK
    )
    aciklama = models.CharField(max_length=255, blank=True)
    olusturan = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="olusturdugu_release_plans",
    )
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    guncelleme_tarihi = models.DateTimeField(auto_now=True)

    _allow_status_transition = False

    class Meta:
        verbose_name = "Sözleşme release planı"
        verbose_name_plural = "Sözleşme release planları"
        ordering = ["-olusturma_tarihi", "-pk"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(toplam_taahhut__gt=0),
                name="contractreleaseplan_taahhut_pozitif",
            ),
            models.CheckConstraint(
                condition=models.Q(birim__in=["ADET", "GRAM"]),
                name="contractreleaseplan_birim_gecerli",
            ),
            models.CheckConstraint(
                condition=models.Q(durum__in=["TASLAK", "AKTIF", "KAPALI"]),
                name="contractreleaseplan_durum_gecerli",
            ),
        ]
        indexes = [
            models.Index(fields=["sozlesme", "durum"]),
            models.Index(fields=["varyant"]),
        ]

    def __str__(self) -> str:
        return (
            f"CRP#{self.pk or '?'} soz={self.sozlesme_id} "
            f"{self.toplam_taahhut} {self.birim}"
        )

    def clean(self):
        super().clean()
        if self.toplam_taahhut is not None and self.toplam_taahhut <= 0:
            raise ValidationError(
                {"toplam_taahhut": "Taahhüt sıfırdan büyük olmalı."}
            )

    def save(self, *args, **kwargs):
        if self._state.adding:
            self.full_clean()
            return super().save(*args, **kwargs)
        if self._allow_status_transition:
            return super().save(*args, **kwargs)
        raise ValidationError(
            "ContractReleasePlan değişmez; durum yalnız release_servisi ile (F5-041)."
        )

    def delete(self, *args, **kwargs):
        raise ValidationError("ContractReleasePlan silinemez.")


class ContractReleaseEvent(models.Model):
    """Append-only dönemsel serbest bırakma kaydı."""

    plan = models.ForeignKey(
        ContractReleasePlan,
        on_delete=models.PROTECT,
        related_name="events",
    )
    miktar = models.DecimalField(max_digits=18, decimal_places=6)
    donem_baslangic = models.DateField()
    donem_bitis = models.DateField()
    aciklama = models.CharField(max_length=255, blank=True)
    olusturan = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="olusturdugu_release_events",
    )
    olusturma_tarihi = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Sözleşme release olayı"
        verbose_name_plural = "Sözleşme release olayları"
        ordering = ["-olusturma_tarihi", "-pk"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(miktar__gt=0),
                name="contractreleaseevent_miktar_pozitif",
            ),
            models.CheckConstraint(
                condition=models.Q(donem_bitis__gte=models.F("donem_baslangic")),
                name="contractreleaseevent_tarih_sirasi",
            ),
        ]

    def __str__(self) -> str:
        return f"CRE#{self.pk or '?'} plan={self.plan_id} {self.miktar}"

    def clean(self):
        super().clean()
        if self.miktar is not None and self.miktar <= 0:
            raise ValidationError({"miktar": "Miktar sıfırdan büyük olmalı."})
        if (
            self.donem_baslangic
            and self.donem_bitis
            and self.donem_bitis < self.donem_baslangic
        ):
            raise ValidationError({"donem_bitis": "Bitiş başlangıçtan önce olamaz."})

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError(
                "ContractReleaseEvent değişmez; UPDATE yasak (F5-041)."
            )
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("ContractReleaseEvent silinemez (F5-041).")
