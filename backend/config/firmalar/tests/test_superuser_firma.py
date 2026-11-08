"""A3 — firma NOT NULL / create_superuser yolları (doğrulama turu)."""

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from firmalar import roles
from firmalar.models import Firma
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.platform_kurulum import ensure_platform_firma

User = get_user_model()


class SuperuserFirmaZorunluluguTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed_role_permissions()
        cls.platform = ensure_platform_firma()

    def test_create_superuser_assigns_platform_firma(self):
        u = User.objects.create_superuser("su1", password="x")
        self.assertTrue(u.is_superuser)
        self.assertEqual(u.firma_id, self.platform.pk)
        self.assertEqual(u.rol, roles.PLATFORM_SUPER)

    def test_plain_create_without_firma_rejected(self):
        u = User(username="nofirma", is_superuser=True, rol=roles.PLATFORM_SUPER)
        u.set_password("x")
        with self.assertRaises(ValidationError):
            u.save()

    def test_objects_create_user_without_firma_rejected(self):
        with self.assertRaises(ValidationError):
            User.objects.create_user(username="cu", password="x")
