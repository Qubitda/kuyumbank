from django.test import TestCase

from bildirim.models import SmtpSettings
from bildirim.services import crypto_servisi, smtp_servisi
from bildirim.services.smtp_servisi import MASK


class SmtpSealTests(TestCase):
    def test_password_sealed_not_plaintext(self):
        smtp = smtp_servisi.get_or_create_singleton()
        smtp_servisi.set_password(smtp, "s3cret-value")
        smtp.save()
        smtp.refresh_from_db()
        self.assertNotIn("s3cret-value", smtp.password_sealed)
        self.assertEqual(crypto_servisi.unseal_password(smtp.password_sealed), "s3cret-value")

    def test_mask_does_not_overwrite(self):
        smtp = smtp_servisi.get_or_create_singleton()
        smtp_servisi.set_password(smtp, "keep-me")
        smtp.save()
        sealed = smtp.password_sealed
        smtp_servisi.set_password(smtp, MASK)
        smtp.save()
        smtp.refresh_from_db()
        self.assertEqual(smtp.password_sealed, sealed)

    def test_singleton_pk(self):
        a = smtp_servisi.get_or_create_singleton()
        b = SmtpSettings(host="x")
        b.save()
        self.assertEqual(SmtpSettings.objects.count(), 1)
        self.assertEqual(a.pk, 1)
