"""Order — alıcı sipariş başlığı (ADR-0011 F4-A9; L-11 bağ OrderLine'da)."""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Order(models.Model):
    class Durum(models.TextChoices):
        OLUSTURULDU = "OLUSTURULDU", "Oluşturuldu"
        IPTAL = "IPTAL", "İptal"

    alici_firma = models.ForeignKey(
        "firmalar.Firma",
        on_delete=models.PROTECT,
        related_name="orders",
        help_text="Tenant sınırı (ADR-0003). Org scope ayrı: sube (ADR-0015).",
    )
    sube = models.ForeignKey(
        "firmalar.OrgBirimi",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="orders",
        help_text="Opsiyonel org/şube (OH-3); tenant değil.",
    )
    checkout_attempt = models.OneToOneField(
        "siparis.CheckoutAttempt",
        on_delete=models.PROTECT,
        related_name="order",
    )
    durum = models.CharField(
        max_length=16, choices=Durum.choices, default=Durum.OLUSTURULDU
    )
    idempotency_key = models.CharField(max_length=64)
    olusturan = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="olusturdugu_orders",
    )
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    guncelleme_tarihi = models.DateTimeField(auto_now=True)

    _allow_status_transition = False

    class Meta:
        verbose_name = "Sipariş"
        verbose_name_plural = "Siparişler"
        ordering = ["-olusturma_tarihi", "-pk"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(durum__in=["OLUSTURULDU", "IPTAL"]),
                name="order_durum_gecerli",
            ),
            models.UniqueConstraint(
                fields=["alici_firma", "idempotency_key"],
                name="order_firma_idempotency_uniq",
            ),
        ]
        indexes = [
            models.Index(fields=["alici_firma", "-olusturma_tarihi"]),
            models.Index(fields=["durum"]),
        ]

    def __str__(self) -> str:
        return f"Order#{self.pk or '?'} {self.durum}"

    def clean(self):
        super().clean()
        firma = getattr(self, "alici_firma", None)
        if firma is not None and not getattr(firma, "alici_mi", False):
            raise ValidationError(
                {"alici_firma": "Sipariş yalnız alıcı firmaya ait olabilir."}
            )
        if self.sube_id and firma is not None and self.sube.firma_id != firma.pk:
            raise ValidationError(
                {"sube": "Org birimi sipariş firmasına ait değil (OH-4)."}
            )

    def save(self, *args, **kwargs):
        if self._state.adding:
            self.full_clean()
            return super().save(*args, **kwargs)
        if self._allow_status_transition:
            update_fields = kwargs.get("update_fields")
            if update_fields is not None and set(update_fields) <= {
                "durum",
                "guncelleme_tarihi",
            }:
                return super().save(*args, **kwargs)
            raise ValidationError(
                "Order geçişi yalnız durum alanı ile yapılır (F4-A9)."
            )
        raise ValidationError(
            "Order değişmez; durum yalnız order_servisi ile."
        )

    def delete(self, *args, **kwargs):
        raise ValidationError("Order silinemez; iptal kullanın.")
