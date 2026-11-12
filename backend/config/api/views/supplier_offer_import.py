"""GAP-F3-04 — POST /supplier/offers/import/preview|commit/."""

from __future__ import annotations

from django.core.exceptions import (
    PermissionDenied as DjangoPermissionDenied,
    ValidationError as DjangoValidationError,
)
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from api.exc import raise_drf
from api.mixins import IdempotencyMixin
from api.permissions import IsAuthenticatedWithFirma
from api.throttles import SupplierRateThrottle
from fiyatlama.services import teklif_import_servisi
from fiyatlama.services.teklif_import_servisi import (
    assert_not_pdf,
    satir_to_dict,
)


def _preview_body(preview) -> dict:
    return {
        "server_now": preview.server_now,
        "satirlar": [satir_to_dict(s) for s in preview.satirlar],
        "hatalar": [
            {"satir_no": h.satir_no, "hata": h.hata} for h in preview.hatalar
        ],
    }


class SupplierOfferImportPreviewView(IdempotencyMixin, APIView):
    """POST multipart file=…csv veya JSON {csv: \"...\"}."""

    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [SupplierRateThrottle]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request):
        cached = self.idempotency_begin(request)
        if cached is not None:
            return cached
        try:
            csv_text = None
            upload = request.FILES.get("file")
            if upload is not None:
                assert_not_pdf(
                    filename=getattr(upload, "name", None),
                    content_type=getattr(upload, "content_type", None),
                )
                raw = upload.read()
                try:
                    csv_text = raw.decode("utf-8-sig")
                except UnicodeDecodeError as exc:
                    raise DjangoValidationError(
                        "CSV UTF-8 olmalıdır."
                    ) from exc
            else:
                data = request.data if isinstance(request.data, dict) else {}
                name_hint = str(data.get("filename") or data.get("name") or "")
                assert_not_pdf(
                    filename=name_hint,
                    content_type=str(data.get("content_type") or ""),
                )
                csv_text = data.get("csv")
                if csv_text is None:
                    raise DjangoValidationError(
                        "file (multipart) veya csv (JSON) zorunlu."
                    )
            preview = teklif_import_servisi.preview_csv(
                request.user, csv_text=str(csv_text)
            )
        except (DjangoValidationError, DjangoPermissionDenied) as exc:
            raise_drf(exc)

        response = Response(_preview_body(preview), status=status.HTTP_200_OK)
        return self.idempotency_commit(request, response)


class SupplierOfferImportCommitView(IdempotencyMixin, APIView):
    """POST JSON {satirlar: [...]} — hepsi geçerliyse taslak teklifler."""

    permission_classes = [IsAuthenticatedWithFirma]
    throttle_classes = [SupplierRateThrottle]

    def post(self, request):
        cached = self.idempotency_begin(request)
        if cached is not None:
            return cached
        data = request.data if isinstance(request.data, dict) else {}
        satirlar = data.get("satirlar")
        try:
            result = teklif_import_servisi.commit_rows(
                request.user, satirlar=satirlar or []
            )
        except DjangoValidationError as exc:
            # message_dict ile hatalar gömülü olabilir
            if hasattr(exc, "message_dict") and isinstance(exc.message_dict, dict):
                md = exc.message_dict
                response = Response(
                    {
                        "detail": md.get("detail")
                        or "Commit reddedildi.",
                        "hatalar": md.get("hatalar") or [],
                        "server_now": None,
                        "created": [],
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
                return self.idempotency_commit(request, response)
            raise_drf(exc)
        except DjangoPermissionDenied as exc:
            raise PermissionDenied(detail=str(exc)) from exc

        body = {
            "server_now": result.server_now,
            "created": result.created,
            "hatalar": [
                {"satir_no": h.satir_no, "hata": h.hata} for h in result.hatalar
            ],
        }
        response = Response(body, status=status.HTTP_201_CREATED)
        return self.idempotency_commit(request, response)
