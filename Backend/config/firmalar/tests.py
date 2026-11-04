from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.test import TestCase

from .kullanici import Kullanici
from .role_services import role_group_name
from .firma import Firma


class KullaniciRolTests(TestCase):
    def setUp(self):
        self.alici = Firma.objects.create(ad="Alıcı AŞ", alici_mi=True)
        self.tedarikci = Firma.objects.create(ad="Tedarikçi AŞ", tedarikci_mi=True)
        self.platform = Firma.objects.create(ad="Platform", platform_mu=True)

    def test_user_requires_firma_and_role(self):
        user = Kullanici(username="eksik")
        with self.assertRaises(ValidationError):
            user.full_clean()

    def test_buyer_role_cannot_be_assigned_to_supplier_only_firm(self):
        user = Kullanici(username="yanlis", firma=self.tedarikci, rol="alici_satinalmaci")
        with self.assertRaises(ValidationError):
            user.full_clean()

    def test_supplier_role_can_be_assigned_to_supplier_firm(self):
        user = Kullanici(username="tedarikci", firma=self.tedarikci, rol="tedarikci_satis")
        user.set_password("test-password")
        user.full_clean()
        user.save()
        self.assertTrue(user.groups.filter(name=role_group_name("tedarikci_satis")).exists())

    def test_platform_role_requires_platform_firm(self):
        user = Kullanici(username="platform", firma=self.platform, rol="platform_ops")
        user.set_password("test-password")
        user.full_clean()
        user.save()
        self.assertTrue(user.groups.filter(name=role_group_name("platform_ops")).exists())

    def test_changing_role_removes_previous_role_group(self):
        user = Kullanici(username="degisen", firma=self.alici, rol="alici_satinalmaci")
        user.set_password("test-password")
        user.save()
        user.rol = "alici_finans"
        user.save()
        self.assertFalse(user.groups.filter(name=role_group_name("alici_satinalmaci")).exists())
        self.assertTrue(user.groups.filter(name=role_group_name("alici_finans")).exists())

    def test_firm_type_cannot_be_changed_while_incompatible_role_is_assigned(self):
        user = Kullanici(username="alici", firma=self.alici, rol="alici_satinalmaci")
        user.set_password("test-password")
        user.save()
        self.alici.alici_mi = False
        with self.assertRaises(ValidationError):
            self.alici.full_clean()
