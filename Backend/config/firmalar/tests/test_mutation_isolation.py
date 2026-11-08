"""A2 senaryo 3–4 — ilişkili nesne / yazma yüzeyi (selectors + model)."""

from django.contrib.auth import get_user_model
from django.http import Http404
from django.test import TestCase

from firmalar import roles
from firmalar.models import Firma, FirmaAdresi
from firmalar.role_permissions import seed_role_permissions
from firmalar.selectors.tenant import assert_same_firma, scope_queryset
from firmalar.services.platform_kurulum import ensure_platform_firma
from firmalar.services.rol_servisi import sync_user_role_groups
from firmalar.services.yetki_servisi import has_perm

User = get_user_model()


class MutationIsolationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed_role_permissions()
        ensure_platform_firma()
        cls.firma_a = Firma.objects.create(
            ad="Mut A", firma_kodu="MUT_A", alici_mi=True, tedarikci_mi=True
        )
        cls.firma_b = Firma.objects.create(
            ad="Mut B", firma_kodu="MUT_B", alici_mi=True, tedarikci_mi=True
        )
        cls.adres_b = FirmaAdresi.objects.create(
            firma=cls.firma_b, tip="merkez", il="Bursa", adres="B"
        )
        cls.user_a = User(
            username="mut_a",
            firma=cls.firma_a,
            rol=roles.ALICI_YONETICI,
        )
        cls.user_a.set_password("x")
        cls.user_a.save()
        sync_user_role_groups(cls.user_a)

    def test_cannot_assert_same_firma_on_b_adres(self):
        with self.assertRaises(Http404):
            assert_same_firma(self.user_a, self.adres_b)

    def test_scoped_queryset_excludes_b_before_update(self):
        qs = scope_queryset(FirmaAdresi.objects.all(), self.user_a)
        self.assertFalse(qs.filter(pk=self.adres_b.pk).exists())

    def test_firma_yonetici_no_approve_urun(self):
        self.assertFalse(has_perm(self.user_a, "urunler.approve_urun"))
        self.assertFalse(has_perm(self.user_a, "firmalar.view_all_tenants"))
