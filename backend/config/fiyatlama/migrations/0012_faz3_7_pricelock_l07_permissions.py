# Dilim 3.7 L-07 — PriceLock lock_quote / lock_quote_on_behalf

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("fiyatlama", "0011_faz3_7_pricelock_l04_ttl_guard"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="pricelock",
            options={
                "ordering": ["-kilit_zamani", "-pk"],
                "permissions": [
                    (
                        "lock_quote",
                        "Kendi firma PriceQuote kayıtları için PriceLock oluşturabilir",
                    ),
                    (
                        "lock_quote_on_behalf",
                        "Alıcı firma adına PriceLock oluşturabilir (platform on-behalf)",
                    ),
                ],
                "verbose_name": "Fiyat kilidi",
                "verbose_name_plural": "Fiyat kilitleri",
            },
        ),
    ]
