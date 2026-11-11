# IdempotencyRecord: purge için created_at indeksi; yinelenen (firma,key) indeksi kaldır

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0001_pre_005_idempotency_record"),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name="idempotencyrecord",
            name="api_idem_firma_key_idx",
        ),
        migrations.AddIndex(
            model_name="idempotencyrecord",
            index=models.Index(
                fields=["created_at"], name="api_idem_created_at_idx"
            ),
        ),
    ]
