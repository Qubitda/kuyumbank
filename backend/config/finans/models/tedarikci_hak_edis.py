"""TedarikciHakEdis — tedarikçi hak ediş iskeleti (F5-022; U-006 QC PASS)."""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class TedarikciHakEdisQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise ValidationError(
            "TedarikciHakEdis QuerySet.update yasak; geçiş yalnız servis."
        )

    def delete(self):
        raise ValidationError("TedarikciHakEdis QuerySet.delete yasak.")


class TedarikciHakEdisManager(models.Manager.from_queryset(TedarikciHakEdisQuerySet)):
    def bulk_update(self, objs, fields, batch_size=None):
        raise ValidationError("TedarikciHakEdis bulk_update yasak.")


class TedarikciHakEdis(models.Model):
    """Oran/üretim tutarı v1'de sabitlenmez (tutar null olabilir)."""

    class Durum(models.TextChoices):
        BEKLEMEDE = "BEKLEMEDE", "Vadeyi bekliyor"
        HAKEDILDI = "HAKEDILDI", "Hak ediş oluştu"
        IPTAL = "IPTAL", "İptal"

    order = models.ForeignKey(
        "siparis.Order",
        on_delete=models.PROTECT,
        related_name="tedarikci_hak_edisleri",
    )
    quality_inspection = models.ForeignKey(
        "kalite.QualityInspection",
        on_delete=models.PROTECT,
        related_name="tedarikci_hak_edisleri",
    )
    tedarikci_firma = models.ForeignKey(
        "firmalar.Firma",
        on_delete=models.PROTECT,
        related_name="hak_edisleri",
    )
    durum = models.CharField(
        max_length=16, choices=Durum.choices, default=Durum.BEKLEMEDE
    )
    gram = models.DecimalField(
        max_digits=18,
        decimal_places=4,
        help_text="FX unpaid_supplier HAS payı (F5-K6).",
    )
    tutar = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Oran politikası sonrası; v1 null (F5-022).",
    )
    para_birimi = models.CharField(max_length=3, blank=True, default="")
    vade_tarihi = models.DateTimeField()
    hak_edis_tarihi = models.DateTimeField(null=True, blank=True)
    idempotency_key = models.CharField(max_length=64)
    aciklama = models.CharField(max_length=255, blank=True)
    olusturan = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="olusturdugu_hak_edisler",
    )
    olusturma_tarihi = models.DateTimeField(default=timezone.now)

    _allow_status_transition = False

    objects = TedarikciHakEdisManager()

    class Meta:
        verbose_name = "Tedarikçi hak ediş"
        verbose_name_plural = "Tedarikçi hak edişleri"
        ordering = ["-olusturma_tarihi", "-pk"]
        permissions = [
            ("manage_hak_edis", "Tedarikçi hak ediş yönetebilir"),
        ]
        indexes = [
            models.Index(fields=["durum", "-olusturma_tarihi"]),
            models.Index(fields=["tedarikci_firma", "durum"]),
            models.Index(fields=["order"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["idempotency_key"],
                name="tedarikcihakedis_idempotency_uniq",
            ),
            models.UniqueConstraint(
                fields=["quality_inspection", "tedarikci_firma"],
                name="tedarikcihakedis_insp_tedarikci_uniq",
            ),
            models.CheckConstraint(
                condition=models.Q(durum__in=["BEKLEMEDE", "HAKEDILDI", "IPTAL"]),
                name="tedarikcihakedis_durum_gecerli",
            ),
            models.CheckConstraint(
                condition=models.Q(gram__gte=0),
                name="tedarikcihakedis_gram_negatif_degil",
            ),
        ]

    def __str__(self) -> str:
        return (
            f"HE#{self.pk or '?'} O#{self.order_id} "
            f"T#{self.tedarikci_firma_id} {self.durum}"
        )

    def save(self, *args, **kwargs):
        if self._state.adding:
            self.full_clean()
            return super().save(*args, **kwargs)
        if self._allow_status_transition:
            return super().save(*args, **kwargs)
        raise ValidationError(
            "TedarikciHakEdis değişmez; geçiş yalnız hak_edis_servisi (F5-022)."
        )

    def delete(self, *args, **kwargs):
        raise ValidationError("TedarikciHakEdis silinemez.")
