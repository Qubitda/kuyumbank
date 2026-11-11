from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("lojistik", "0003_f6_030_return_request"),
    ]

    operations = [
        migrations.AddField(
            model_name="returnrequest",
            name="idempotency_key",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
        migrations.AddConstraint(
            model_name="returnrequest",
            constraint=models.UniqueConstraint(
                condition=~models.Q(idempotency_key=""),
                fields=("order", "idempotency_key"),
                name="returnrequest_order_idempotency_uniq",
            ),
        ),
    ]
