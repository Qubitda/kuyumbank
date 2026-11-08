from django.db import models

from .taban import TanimTaban


class SatisKanali(TanimTaban):
    quote_ttl_saniye = models.PositiveIntegerField(
        "Quote TTL (sn)",
        null=True,
        blank=True,
        help_text="ADR-0008 B-03: kanal bazlı quote geçerliliği. Boşsa quote üretilmez (3.5).",
    )

    class Meta:
        verbose_name = "Satış kanalı"
        verbose_name_plural = "Satış kanalları"
        ordering = ["sira", "ad"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quote_ttl_saniye__isnull=True)
                | models.Q(quote_ttl_saniye__gt=0),
                name="satis_kanali_quote_ttl_pozitif",
            ),
        ]
