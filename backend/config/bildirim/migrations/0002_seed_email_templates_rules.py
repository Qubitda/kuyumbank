from django.db import migrations


def forwards(apps, schema_editor):
    # Servis katmanı kullan (idempotent seed).
    from bildirim.services.seed_servisi import seed_templates_and_rules

    seed_templates_and_rules()


def backwards(apps, schema_editor):
    EmailTemplate = apps.get_model("bildirim", "EmailTemplate")
    NotificationRule = apps.get_model("bildirim", "NotificationRule")
    NotificationRule.objects.all().delete()
    EmailTemplate.objects.filter(sistem_mi=True).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("bildirim", "0001_initial_email_bildirim"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
