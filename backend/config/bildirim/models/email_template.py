"""E-posta şablonları."""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import models


class EmailTemplate(models.Model):
    kod = models.SlugField(max_length=64, unique=True)
    ad = models.CharField(max_length=120)
    subject = models.CharField(max_length=255)
    html_body = models.TextField()
    aktif = models.BooleanField(default=True)
    sistem_mi = models.BooleanField(
        default=False,
        help_text="Seed sistem şablonu; silinemez.",
    )
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    guncelleme_tarihi = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "E-posta şablonu"
        verbose_name_plural = "E-posta şablonları"
        ordering = ["kod"]
        permissions = [
            ("manage_email_template", "E-posta şablonlarını yönetebilir"),
        ]

    def __str__(self) -> str:
        return f"{self.kod} — {self.ad}"

    def clean(self):
        super().clean()
        if not (self.kod or "").strip():
            raise ValidationError({"kod": "kod zorunlu."})
        if not (self.subject or "").strip():
            raise ValidationError({"subject": "Konu zorunlu."})

    def delete(self, *args, **kwargs):
        if self.sistem_mi:
            raise ValidationError("Sistem şablonu silinemez.")
        return super().delete(*args, **kwargs)
