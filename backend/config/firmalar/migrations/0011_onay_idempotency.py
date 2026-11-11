from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("firmalar", "0010_audit_on_behalf_of"),
    ]

    operations = [
        migrations.AddField(
            model_name="onaytalebi",
            name="idempotency_key",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
        migrations.AddConstraint(
            model_name="onaytalebi",
            constraint=models.UniqueConstraint(
                condition=~models.Q(idempotency_key=""),
                fields=("firma", "idempotency_key"),
                name="onaytalebi_firma_idempotency_uniq",
            ),
        ),
    ]
