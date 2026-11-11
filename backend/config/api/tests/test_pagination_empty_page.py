"""Sayfa taşması → 404 (sessizce son sayfaya düşmez)."""

from django.test import RequestFactory, TestCase
from rest_framework.exceptions import NotFound

from api.pagination import paginate_queryset
from firmalar.models import Firma


class PaginationEmptyPageTests(TestCase):
    def test_out_of_range_page_raises_not_found(self):
        Firma.objects.create(ad="P1", firma_kodu="PAG1", alici_mi=True)
        qs = Firma.objects.all().order_by("pk")
        req = RequestFactory().get("/x/", {"page": "999", "page_size": "10"})
        # DRF Request sarması gerekmez; query_params yok → QueryDict üzerinden
        from rest_framework.request import Request

        request = Request(req)
        with self.assertRaises(NotFound):
            paginate_queryset(request, qs, present=lambda f: {"id": f.pk})
