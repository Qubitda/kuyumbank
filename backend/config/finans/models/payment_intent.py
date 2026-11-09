"""PaymentIntent — Order tahsilat adayı (F5-012)."""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class PaymentIntent(models.Model):
    class Durum(models.TextChoices):
        BEKLEMEDE = "BEKLEMEDE", "Beklemede"
        BASARILI = "BASARILI", "Başarılı"
        IPTAL = "IPTAL", "İptal"
        BASARISIZ = "BASARISIZ", "Başarısız"

    order = models.ForeignKey(
        "siparis.Order",
        on_delete=models.PROTECT,
        related_name="payment_intents",
    )
    alici_firma = models.ForeignKey(
        "firmalar.Firma",
        on_delete=models.PROTECT,
        related_name="payment_intents",
        help_text="Denormalize tenant; order.alici_firma ile eşit.",
    )
    tutar = models.DecimalField(max_digits=18, decimal_places=2)
    para_birimi = models.CharField(max_length=3)
    durum = models.CharField(
        max_length=16, choices=Durum.choices, default=Durum.BEKLEMEDE
    )
    idempotency_key = models.CharField(max_length=64)
    ledger_entry = models.ForeignKey(
        "finans.LedgerEntry",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="payment_intents",
    )
    olusturan = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="olusturdugu_payment_intents",
    )
    olusturma_tarihi = models.DateTimeField(default=timezone.now)
    guncelleme_tarihi = models.DateTimeField(auto_now=True)

    _allow_status_transition = False

    class Meta:
        verbose_name = "Ödeme niyeti"
        verbose_name_plural = "Ödeme niyetleri"
        ordering = ["-olusturma_tarihi", "-pk"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(tutar__gt=0),
                name="paymentintent_tutar_pozitif",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    durum__in=["BEKLEMEDE", "BASARILI", "IPTAL", "BASARISIZ"]
                ),
                name="paymentintent_durum_gecerli",
            ),
            models.UniqueConstraint(
                fields=["alici_firma", "idempotency_key"],
                name="paymentintent_firma_idempotency_uniq",
            ),
            # Çift tahsilat yok: sipariş başına en fazla bir BASARILI
            models.UniqueConstraint(
                fields=["order"],
                condition=models.Q(durum="BASARILI"),
                name="paymentintent_order_basarili_uniq",
            ),
        ]
        indexes = [
            models.Index(fields=["alici_firma", "-olusturma_tarihi"]),
            models.Index(fields=["order", "durum"]),
        ]

    def __str__(self) -> str:
        return f"PI#{self.pk or '?'} {self.durum} {self.tutar} {self.para_birimi}"

    def clean(self):
        super().clean()
        if self.tutar is not None and self.tutar <= 0:
            raise ValidationError({"tutar": "Tutar sıfırdan büyük olmalı."})
        pb = (self.para_birimi or "").strip().upper()
        if len(pb) != 3 or not pb.isalpha():
            raise ValidationError(
                {"para_birimi": "ISO 4217 para birimi zorunlu (3 harf)."}
            )
        self.para_birimi = pb
        if (
            self.order_id
            and self.alici_firma_id
            and self.order.alici_firma_id != self.alici_firma_id
        ):
            raise ValidationError(
                {"alici_firma": "alici_firma, order.alici_firma ile eşit olmalı."}
            )

    def save(self, *args, **kwargs):
        if self._state.adding:
            self.full_clean()
            return super().save(*args, **kwargs)
        if self._allow_status_transition:
            return super().save(*args, **kwargs)
        raise ValidationError(
            "PaymentIntent değişmez; durum yalnız payment_servisi ile (F5-012)."
        )

    def delete(self, *args, **kwargs):
        raise ValidationError("PaymentIntent silinemez; iptal kullanın.")
