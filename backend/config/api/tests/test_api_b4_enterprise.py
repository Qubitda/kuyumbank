"""API-B4 — org / onay / RFQ HTTP + concurrency (PostgreSQL)."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TransactionTestCase
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase

from api.masking import assert_masked
from firmalar import roles
from firmalar.models import OnayTalebi, OrgBirimi, OrgUyeligi
from firmalar.role_permissions import seed_role_permissions
from firmalar.services import onay_servisi, org_servisi
from firmalar.services.rol_servisi import sync_user_role_groups
from siparis.models import RFQ, RFQMessage, RFQRevizyon
from siparis.services import rfq_servisi
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin

User = get_user_model()


class B4FixtureMixin(CheckoutFixtureMixin):
    @classmethod
    def _build_b4_world(cls):
        cls._build_checkout_world()
        seed_role_permissions()
        sync_user_role_groups(cls.buyer)
        cls.mgr = User(
            username="b4_mgr",
            firma=cls.alici,
            rol=roles.ALICI_YONETICI,
            is_staff=True,
        )
        cls.mgr.set_password("x")
        cls.mgr.save()
        sync_user_role_groups(cls.mgr)
        cls.approver = User(
            username="b4_appr",
            firma=cls.alici,
            rol=roles.ALICI_ONAYLAYICI,
            is_staff=True,
        )
        cls.approver.set_password("x")
        cls.approver.save()
        sync_user_role_groups(cls.approver)
        # Yayınlı katalog varyantı (B2 catalog kuralı)
        urun = cls.varyant.urun
        urun.yayin_durumu = "aktif"
        urun.onay_durumu = "onayli"
        urun.save(update_fields=["yayin_durumu", "onay_durumu"])
        cls.varyant.aktif = True
        cls.varyant.save(update_fields=["aktif"])


class ApiB4EnterpriseTests(B4FixtureMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_b4_world()

    def setUp(self):
        self.api = APIClient()

    def _idem(self, key):
        return {"HTTP_IDEMPOTENCY_KEY": key}

    def test_org_create_member_tenant_rbac(self):
        self.api.force_authenticate(user=self.mgr)
        res = self.api.post(
            reverse("api-org-list"),
            {"kod": "B4HQ", "ad": "Merkez"},
            format="json",
            **self._idem("b4-org-1"),
        )
        self.assertEqual(res.status_code, 201, res.content)
        body = res.json()
        self.assertEqual(body["kod"], "B4HQ")
        self.assertIn("add_member", body["allowed_actions"])
        assert_masked(body)
        oid = body["id"]

        mem = self.api.post(
            reverse("api-org-members", kwargs={"pk": oid}),
            {"kullanici_id": self.buyer.pk},
            format="json",
            **self._idem("b4-org-m1"),
        )
        self.assertEqual(mem.status_code, 201, mem.content)
        self.assertEqual(
            OrgUyeligi.objects.filter(
                org_birimi_id=oid, kullanici=self.buyer
            ).count(),
            1,
        )

        # Aynı key + aynı body → tek kayıt
        again = self.api.post(
            reverse("api-org-list"),
            {"kod": "B4HQ", "ad": "Merkez"},
            format="json",
            **self._idem("b4-org-1"),
        )
        self.assertEqual(again.status_code, 201)
        self.assertEqual(again.json()["id"], oid)
        self.assertEqual(
            OrgBirimi.objects.filter(firma=self.alici, kod="B4HQ").count(), 1
        )

        # Aynı key + farklı body → 409
        conflict = self.api.post(
            reverse("api-org-list"),
            {"kod": "OTHER", "ad": "X"},
            format="json",
            **self._idem("b4-org-1"),
        )
        self.assertEqual(conflict.status_code, 409)
        self.assertEqual(conflict.json().get("code"), "idempotency_conflict")

        # Satınalmacı manage_org yok → 403
        self.api.force_authenticate(user=self.buyer)
        deny = self.api.post(
            reverse("api-org-list"),
            {"kod": "X", "ad": "X"},
            format="json",
            **self._idem("b4-org-deny"),
        )
        self.assertEqual(deny.status_code, 403)

        # Tedarikçi çapraz org → 404 (scope dışı)
        self.api.force_authenticate(user=self.ted_user)
        cross = self.api.get(reverse("api-org-detail", kwargs={"pk": oid}))
        self.assertEqual(cross.status_code, 404)

        # Çapraz firma kullanıcı ekleme → 404
        self.api.force_authenticate(user=self.mgr)
        cross_mem = self.api.post(
            reverse("api-org-members", kwargs={"pk": oid}),
            {"kullanici_id": self.ted_user.pk},
            format="json",
            **self._idem("b4-org-cross-m"),
        )
        self.assertEqual(cross_mem.status_code, 404)

    def test_org_list_pagination_nx2(self):
        self.api.force_authenticate(user=self.mgr)
        for i in range(3):
            self.api.post(
                reverse("api-org-list"),
                {"kod": f"P{i}", "ad": f"P{i}"},
                format="json",
                **self._idem(f"b4-org-p{i}"),
            )
        page = self.api.get(
            reverse("api-org-list"), {"page": 1, "page_size": 2}
        )
        self.assertEqual(page.status_code, 200)
        body = page.json()
        self.assertEqual(body["page_size"], 2)
        self.assertLessEqual(len(body["results"]), 2)
        self.assertIn("count", body)
        huge = self.api.get(
            reverse("api-org-list"), {"page_size": 500}
        )
        self.assertEqual(huge.status_code, 200)
        self.assertLessEqual(huge.json()["page_size"], 100)

    def test_approval_flow_masked_idempotency(self):
        self.api.force_authenticate(user=self.approver)
        create = self.api.post(
            reverse("api-approval-list"),
            {"tutar": "150.00", "para_birimi": "TRY", "gerekce": "limit asi"},
            format="json",
            **self._idem("b4-ot-1"),
        )
        self.assertEqual(create.status_code, 201, create.content)
        body = create.json()
        self.assertEqual(body["tutar"], "150.00")
        self.assertIn("submit", body["allowed_actions"])
        self.assertNotIn("karar_veren", body)
        assert_masked(body)
        oid = body["id"]

        sub = self.api.post(
            reverse("api-approval-submit", kwargs={"pk": oid}),
            {},
            format="json",
            **self._idem("b4-ot-s"),
        )
        self.assertEqual(sub.status_code, 200)
        self.assertEqual(sub.json()["durum"], OnayTalebi.Durum.BEKLEMEDE)

        ap = self.api.post(
            reverse("api-approval-approve", kwargs={"pk": oid}),
            {},
            format="json",
            **self._idem("b4-ot-a"),
        )
        self.assertEqual(ap.status_code, 200)
        self.assertEqual(ap.json()["durum"], OnayTalebi.Durum.ONAYLANDI)

        # Reject idempotency conflict path (yeni talep)
        create2 = self.api.post(
            reverse("api-approval-list"),
            {"tutar": "20.00", "para_birimi": "TRY"},
            format="json",
            **self._idem("b4-ot-2"),
        )
        oid2 = create2.json()["id"]
        self.api.post(
            reverse("api-approval-submit", kwargs={"pk": oid2}),
            {},
            format="json",
            **self._idem("b4-ot-2s"),
        )
        rej = self.api.post(
            reverse("api-approval-reject", kwargs={"pk": oid2}),
            {"reason": "yetersiz"},
            format="json",
            **self._idem("b4-ot-2r"),
        )
        self.assertEqual(rej.status_code, 200)
        self.assertEqual(rej.json()["durum"], OnayTalebi.Durum.REDDEDILDI)
        again = self.api.post(
            reverse("api-approval-reject", kwargs={"pk": oid2}),
            {"reason": "yetersiz"},
            format="json",
            **self._idem("b4-ot-2r"),
        )
        self.assertEqual(again.status_code, 200)
        conflict = self.api.post(
            reverse("api-approval-reject", kwargs={"pk": oid2}),
            {"reason": "farkli"},
            format="json",
            **self._idem("b4-ot-2r"),
        )
        self.assertEqual(conflict.status_code, 409)

        # Tedarikçi rol kapısı → 403 (B2 Order/Catalog deseni)
        self.api.force_authenticate(user=self.ted_user)
        deny = self.api.get(reverse("api-approval-list"))
        self.assertEqual(deny.status_code, 403)

    def test_rfq_flow_blind_message_variant(self):
        self.api.force_authenticate(user=self.buyer)
        create = self.api.post(
            reverse("api-rfq-list"),
            {
                "baslik": "B4 RFQ",
                "talep_tipi": "OZEL_URETIM",
                "lines": [
                    {
                        "aciklama": "özel bilezik",
                        "miktar": "5",
                        "birim": "ADET",
                        "varyant_id": self.varyant.pk,
                    }
                ],
            },
            format="json",
            **self._idem("b4-rfq-1"),
        )
        self.assertEqual(create.status_code, 201, create.content)
        body = create.json()
        self.assertEqual(body["talep_tipi"], RFQ.TalepTipi.OZEL_URETIM)
        self.assertEqual(Decimal(body["lines"][0]["miktar"]), Decimal("5"))
        self.assertIn("send", body["allowed_actions"])
        self.assertGreaterEqual(len(body["revizyonlar"]), 1)
        self.assertNotIn("olusturan", body)
        self.assertNotIn("alici_firma", body)
        assert_masked(body)
        rid = body["id"]

        send = self.api.post(
            reverse("api-rfq-send", kwargs={"pk": rid}),
            {},
            format="json",
            **self._idem("b4-rfq-s"),
        )
        self.assertEqual(send.status_code, 200)
        self.assertEqual(send.json()["durum"], RFQ.Durum.GONDERILDI)

        msg = self.api.post(
            reverse("api-rfq-message", kwargs={"pk": rid}),
            {"govde": "Platform sorusu"},
            format="json",
            **self._idem("b4-rfq-m"),
        )
        self.assertEqual(msg.status_code, 200)
        m0 = msg.json()["messages"][0]
        self.assertEqual(m0["gonderen_rol"], roles.ALICI_SATINALMACI)
        self.assertNotIn("olusturan", m0)

        rev = self.api.post(
            reverse("api-rfq-revision", kwargs={"pk": rid}),
            {"ozet": "Taş rengi değişti"},
            format="json",
            **self._idem("b4-rfq-r"),
        )
        self.assertEqual(rev.status_code, 200)
        self.assertGreaterEqual(len(rev.json()["revizyonlar"]), 2)

        # Görünmeyen (pasif) varyant = olmayan ile aynı hata (varlık sızdırılmaz)
        self.varyant.aktif = False
        self.varyant.save(update_fields=["aktif"])
        bad_pub = self.api.post(
            reverse("api-rfq-list"),
            {
                "baslik": "bad",
                "lines": [
                    {
                        "aciklama": "x",
                        "miktar": "1",
                        "varyant_id": self.varyant.pk,
                    }
                ],
            },
            format="json",
            **self._idem("b4-rfq-bad-pub"),
        )
        self.assertEqual(bad_pub.status_code, 400)
        missing = self.api.post(
            reverse("api-rfq-list"),
            {
                "baslik": "bad2",
                "lines": [
                    {"aciklama": "x", "miktar": "1", "varyant_id": 99999999}
                ],
            },
            format="json",
            **self._idem("b4-rfq-bad-miss"),
        )
        self.assertEqual(missing.status_code, 400)
        self.assertEqual(bad_pub.json()["detail"], missing.json()["detail"])
        self.assertEqual(bad_pub.json()["detail"], "Varyant bulunamadı.")
        self.varyant.aktif = True
        self.varyant.save(update_fields=["aktif"])

        # Tedarikçi → 403 (rol kapısı; B2 Order/Catalog)
        self.api.force_authenticate(user=self.ted_user)
        cross = self.api.get(reverse("api-rfq-detail", kwargs={"pk": rid}))
        self.assertEqual(cross.status_code, 403)

        # RFQ create idempotency conflict
        self.api.force_authenticate(user=self.buyer)
        payload = {
            "baslik": "Idem RFQ",
            "lines": [{"aciklama": "a", "miktar": "1", "birim": "ADET"}],
        }
        a = self.api.post(
            reverse("api-rfq-list"),
            payload,
            format="json",
            **self._idem("b4-rfq-idem"),
        )
        self.assertEqual(a.status_code, 201)
        b = self.api.post(
            reverse("api-rfq-list"),
            payload,
            format="json",
            **self._idem("b4-rfq-idem"),
        )
        self.assertEqual(b.status_code, 201)
        self.assertEqual(a.json()["id"], b.json()["id"])
        c = self.api.post(
            reverse("api-rfq-list"),
            {**payload, "baslik": "Other"},
            format="json",
            **self._idem("b4-rfq-idem"),
        )
        self.assertEqual(c.status_code, 409)


class ApiB4ConcurrencyTests(B4FixtureMixin, TransactionTestCase):
    def setUp(self):
        self._build_b4_world()

    def _parallel_post(self, user_pk, url, data, key, n=4):
        def worker(payload):
            connection.close()
            user = User.objects.get(pk=user_pk)
            api = APIClient()
            api.force_authenticate(user=user)
            return api.post(
                url, payload, format="json", HTTP_IDEMPOTENCY_KEY=key
            )

        results = []
        with ThreadPoolExecutor(max_workers=n) as pool:
            futs = [pool.submit(worker, data) for _ in range(n)]
            for f in as_completed(futs):
                results.append(f.result())
        return results

    def test_concurrent_org_create_one(self):
        url = reverse("api-org-list")
        results = self._parallel_post(
            self.mgr.pk,
            url,
            {"kod": "CONC", "ad": "Conc"},
            "b4c-org-1",
            n=4,
        )
        self.assertTrue(
            all(r.status_code == 201 for r in results),
            [r.status_code for r in results],
        )
        ids = {r.json()["id"] for r in results}
        self.assertEqual(len(ids), 1)
        self.assertEqual(
            OrgBirimi.objects.filter(firma=self.alici, kod="CONC").count(), 1
        )

    def test_concurrent_org_members_one(self):
        ob = org_servisi.olustur_birim(
            actor=self.mgr, firma=self.alici, kod="MEM", ad="Mem"
        )
        url = reverse("api-org-members", kwargs={"pk": ob.pk})
        results = self._parallel_post(
            self.mgr.pk,
            url,
            {"kullanici_id": self.buyer.pk},
            "b4c-org-m",
            n=4,
        )
        self.assertTrue(all(r.status_code == 201 for r in results))
        self.assertEqual(
            OrgUyeligi.objects.filter(
                org_birimi=ob, kullanici=self.buyer
            ).count(),
            1,
        )

    def test_concurrent_approval_approve_once(self):
        ot = onay_servisi.olustur(
            actor=self.approver,
            firma=self.alici,
            tutar=Decimal("50.00"),
        )
        ot = onay_servisi.beklemede_al(actor=self.approver, onay=ot)
        url = reverse("api-approval-approve", kwargs={"pk": ot.pk})
        results = self._parallel_post(
            self.approver.pk, url, {}, "b4c-ot-a", n=4
        )
        self.assertTrue(all(r.status_code == 200 for r in results))
        ot.refresh_from_db()
        self.assertEqual(ot.durum, OnayTalebi.Durum.ONAYLANDI)

    def test_concurrent_approval_reject_once(self):
        ot = onay_servisi.olustur(
            actor=self.approver,
            firma=self.alici,
            tutar=Decimal("30.00"),
        )
        ot = onay_servisi.beklemede_al(actor=self.approver, onay=ot)
        url = reverse("api-approval-reject", kwargs={"pk": ot.pk})
        results = self._parallel_post(
            self.approver.pk,
            url,
            {"reason": "no"},
            "b4c-ot-r",
            n=4,
        )
        self.assertTrue(all(r.status_code == 200 for r in results))
        ot.refresh_from_db()
        self.assertEqual(ot.durum, OnayTalebi.Durum.REDDEDILDI)

    def test_concurrent_rfq_create_one(self):
        url = reverse("api-rfq-list")
        payload = {
            "baslik": "Conc RFQ",
            "lines": [{"aciklama": "x", "miktar": "1", "birim": "ADET"}],
        }
        results = self._parallel_post(
            self.buyer.pk, url, payload, "b4c-rfq-1", n=4
        )
        self.assertTrue(
            all(r.status_code == 201 for r in results),
            [r.content for r in results],
        )
        ids = {r.json()["id"] for r in results}
        self.assertEqual(len(ids), 1)
        self.assertEqual(
            RFQ.objects.filter(alici_firma=self.alici, baslik="Conc RFQ").count(),
            1,
        )

    def test_concurrent_rfq_message_one(self):
        rfq = rfq_servisi.olustur(
            actor=self.buyer,
            baslik="Msg race",
            line_specs=[{"aciklama": "x", "miktar": Decimal("1"), "birim": "ADET"}],
        )
        rfq = rfq_servisi.gonder(actor=self.buyer, rfq=rfq)
        url = reverse("api-rfq-message", kwargs={"pk": rfq.pk})
        results = self._parallel_post(
            self.buyer.pk,
            url,
            {"govde": "aynı mesaj gövdesi"},
            "b4c-rfq-m",
            n=4,
        )
        self.assertTrue(all(r.status_code == 200 for r in results))
        self.assertEqual(RFQMessage.objects.filter(rfq=rfq).count(), 1)

    def test_concurrent_rfq_revision_one(self):
        rfq = rfq_servisi.olustur(
            actor=self.buyer,
            baslik="Rev race",
            line_specs=[{"aciklama": "x", "miktar": Decimal("1"), "birim": "ADET"}],
            talep_tipi=RFQ.TalepTipi.OZEL_URETIM,
        )
        url = reverse("api-rfq-revision", kwargs={"pk": rfq.pk})
        before = RFQRevizyon.objects.filter(rfq=rfq).count()
        results = self._parallel_post(
            self.buyer.pk,
            url,
            {"ozet": "revizyon yarisi"},
            "b4c-rfq-r",
            n=4,
        )
        self.assertTrue(all(r.status_code == 200 for r in results))
        self.assertEqual(
            RFQRevizyon.objects.filter(rfq=rfq).count(), before + 1
        )
