# Generated manually for ADR-0021 AA-9 — act-as audit on_behalf_of

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("firmalar", "0009_act_as_user_perm"),
    ]

    operations = [
        migrations.AddField(
            model_name="auditolay",
            name="on_behalf_of",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="audit_olaylari_on_behalf",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
