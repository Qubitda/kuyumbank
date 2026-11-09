"""F10-011/012/013 — org scope, harcama limiti, onay SM."""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase

from firmalar import roles
from firmalar.models import HarcamaLimiti, OnayTalebi
from firmalar.role_permissions import seed_role_permissions
from firmalar.services import limiti_servisi, onay_servisi, org_servisi
from firmalar.services.rol_servisi import sync_user_role_groups
from firmalar.services.yetki_servisi import require_org_scope
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin

User = get_user_model()


class LimitOnayF10Tests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()
        seed_role_permissions()
        cls.mgr = User(
            username="lim_mgr",
            firma=cls.alici,
            rol=roles.ALICI_YONETICI,
            is_staff=True,
        )
        cls.mgr.set_password("x")
        cls.mgr.save()
        sync_user_role_groups(cls.mgr)

        cls.approver = User(
            username="lim_appr",
            firma=cls.alici,
            rol=roles.ALICI_ONAYLAYICI,
            is_staff=True,
        )
        cls.approver.set_password("x")
        cls.approver.save()
        sync_user_role_groups(cls.approver)

        cls.org = org_servisi.olustur_birim(
            actor=cls.mgr, firma=cls.alici, kod="LIM", ad="Limit şube"
        )

    def test_require_org_scope_membership(self):
        require_org_scope(self.mgr, self.org)  # manage_org
        with self.assertRaises(PermissionDenied):
            require_org_scope(self.buyer, self.org)
        org_servisi.uye_ekle(
            actor=self.mgr, org_birimi=self.org, kullanici=self.buyer
        )
        require_org_scope(self.buyer, self.org)

    def test_assert_musait_blocks(self):
        limiti_servisi.kaydet_limit(
            actor=self.mgr,
            firma=self.alici,
            tutar=Decimal("10.00"),
            para_birimi="TRY",
            donem=HarcamaLimiti.Donem.SIPARIS,
        )
        with self.assertRaises(ValidationError):
            limiti_servisi.assert_musait(
                firma=self.alici,
                tutar=Decimal("100.00"),
                para_birimi="TRY",
            )
        limiti_servisi.assert_musait(
            firma=self.alici,
            tutar=Decimal("5.00"),
            para_birimi="TRY",
        )

    def test_onay_sm(self):
        ot = onay_servisi.olustur(
            actor=self.approver,
            firma=self.alici,
            tutar=Decimal("50.00"),
            para_birimi="TRY",
            org_birimi=self.org,
        )
        self.assertEqual(ot.durum, OnayTalebi.Durum.TASLAK)
        ot = onay_servisi.beklemede_al(actor=self.approver, onay=ot)
        self.assertEqual(ot.durum, OnayTalebi.Durum.BEKLEMEDE)
        ot = onay_servisi.onayla(actor=self.approver, onay=ot)
        self.assertEqual(ot.durum, OnayTalebi.Durum.ONAYLANDI)
        with self.assertRaises(ValidationError):
            onay_servisi.reddet(actor=self.approver, onay=ot)
