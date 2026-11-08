"""Rol matrisi Django view/change izinlerini gruplara seed eder."""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase

from firmalar import roles
from firmalar.models import Firma
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.rol_servisi import sync_user_role_groups
from firmalar.services.yetki_servisi import has_perm

User = get_user_model()


class RoleAdminPermSeedTests(TestCase):
    def test_tedarikci_sahip_gets_view_varyant_via_group_not_user_perm(self):
        seed_role_permissions()
        firma = Firma.objects.create(
            ad="Seed Ted", firma_kodu="SEEDT", tedarikci_mi=True
        )
        user = User(username="seed_ted", firma=firma, rol=roles.TEDARIKCI_SAHIP)
        user.set_password("x")
        user.save()
        sync_user_role_groups(user)

        self.assertFalse(user.user_permissions.filter(codename="view_varyant").exists())
        self.assertTrue(has_perm(user, "urunler.view_varyant"))
        self.assertTrue(has_perm(user, "urunler.change_varyant"))

    def test_approve_eslestirme_on_catalog_group(self):
        seed_role_permissions()
        self.assertTrue(
            Permission.objects.filter(
                content_type__app_label="fiyatlama",
                codename="approve_eslestirme",
            ).exists()
        )
        from django.contrib.auth.models import Group
        from firmalar import roles as R

        g = Group.objects.get(name=f"rol:{R.PLATFORM_CATALOG}")
        self.assertTrue(
            g.permissions.filter(codename="approve_eslestirme").exists()
        )
