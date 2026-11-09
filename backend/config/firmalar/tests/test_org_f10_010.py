"""F10-010 — OrgBirimi / OrgUyeligi / Order.sube null OK; tenant izolasyon."""

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied, ValidationError
from django.test import TestCase

from firmalar import roles
from firmalar.models import Firma, OrgBirimi, OrgUyeligi
from firmalar.role_permissions import seed_role_permissions
from firmalar.selectors.org import get_org_for_actor, scope_org_queryset
from firmalar.services import org_servisi
from firmalar.services.rol_servisi import sync_user_role_groups
from siparis.models import Cart, Order
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin

User = get_user_model()


class OrgF10010Tests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()
        seed_role_permissions()
        cls.mgr = User(
            username="org_mgr",
            firma=cls.alici,
            rol=roles.ALICI_YONETICI,
            is_staff=True,
        )
        cls.mgr.set_password("x")
        cls.mgr.save()
        sync_user_role_groups(cls.mgr)

        cls.other = Firma.objects.create(
            ad="ORGOTHER", firma_kodu="ORGOTHER", alici_mi=True
        )
        cls.intruder = User(
            username="org_intr",
            firma=cls.other,
            rol=roles.ALICI_YONETICI,
            is_staff=True,
        )
        cls.intruder.set_password("x")
        cls.intruder.save()
        sync_user_role_groups(cls.intruder)

    def test_olustur_birim_ve_uye(self):
        ob = org_servisi.olustur_birim(
            actor=self.mgr, firma=self.alici, kod="HQ", ad="Merkez"
        )
        self.assertEqual(ob.firma_id, self.alici.pk)
        uy = org_servisi.uye_ekle(
            actor=self.mgr, org_birimi=ob, kullanici=self.buyer
        )
        self.assertEqual(uy.org_birimi_id, ob.pk)
        self.assertEqual(
            OrgUyeligi.objects.filter(kullanici=self.buyer, org_birimi=ob).count(),
            1,
        )

    def test_cross_tenant_selector_404(self):
        ob = org_servisi.olustur_birim(
            actor=self.mgr, firma=self.alici, kod="BR1", ad="Şube"
        )
        with self.assertRaises(ObjectDoesNotExist):
            get_org_for_actor(self.intruder, ob.pk)
        self.assertFalse(
            scope_org_queryset(OrgBirimi.objects.all(), self.intruder)
            .filter(pk=ob.pk)
            .exists()
        )

    def test_cross_firma_uye_rejected(self):
        ob = org_servisi.olustur_birim(
            actor=self.mgr, firma=self.alici, kod="BR2", ad="Şube2"
        )
        with self.assertRaises(ValidationError):
            org_servisi.uye_ekle(
                actor=self.mgr, org_birimi=ob, kullanici=self.intruder
            )

    def test_order_sube_null_ok(self):
        # Model alanı nullable — migration sonrası null kaydedilebilir
        self.assertTrue(
            Order._meta.get_field("sube").null
            and Order._meta.get_field("sube").blank
        )
        self.assertTrue(
            Cart._meta.get_field("sube").null
            and Cart._meta.get_field("sube").blank
        )

    def test_satinalmaci_cannot_manage_org(self):
        with self.assertRaises(PermissionDenied):
            org_servisi.olustur_birim(
                actor=self.buyer, firma=self.alici, kod="X", ad="X"
            )
