"""has_perm: is_active=False ve firma.aktif=False → False."""

from django.contrib.auth import get_user_model
from django.test import TestCase

from firmalar import roles
from firmalar.models import Firma
from firmalar.role_permissions import P, seed_role_permissions
from firmalar.services.platform_kurulum import ensure_platform_firma
from firmalar.services.rol_servisi import sync_user_role_groups
from firmalar.services.yetki_servisi import has_perm

User = get_user_model()


class HasPermActiveTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed_role_permissions()
        cls.platform = ensure_platform_firma()
        cls.firma = Firma.objects.create(
            ad="Aktif Co", firma_kodu="ACT1", tedarikci_mi=True, aktif=True
        )
        cls.user = User(
            username="act_u",
            firma=cls.firma,
            rol=roles.TEDARIKCI_SAHIP,
            is_active=True,
        )
        cls.user.set_password("x")
        cls.user.save()
        sync_user_role_groups(cls.user)

    def test_active_user_has_submit(self):
        self.assertTrue(has_perm(self.user, P["submit_urun"]))

    def test_inactive_user_denied(self):
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])
        self.assertFalse(has_perm(self.user, P["submit_urun"]))

    def test_inactive_firma_denied(self):
        self.firma.aktif = False
        self.firma.save(update_fields=["aktif"])
        # refresh user.firma
        u = User.objects.select_related("firma").get(pk=self.user.pk)
        self.assertFalse(has_perm(u, P["submit_urun"]))
