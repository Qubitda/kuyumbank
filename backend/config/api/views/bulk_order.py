"""F4-081 — Bulk Order CSV POST (Idempotency-Key)."""

from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from api.mixins import IdempotencyMixin
from api.permissions import IsBuyerCommerceWrite
from siparis.services import bulk_servisi
from tanimlar.models import SatisKanali


class BulkOrderCreateView(IdempotencyMixin, APIView):
    """POST /api/v1/bulk-orders/ — CSV veya rows → Order; key zorunlu."""

    permission_classes = [IsBuyerCommerceWrite]

    def post(self, request):
        cached = self.idempotency_begin(request)
        if cached is not None:
            return cached

        key = request._idempotency["key"]
        data = request.data if isinstance(request.data, dict) else {}
        kanal_id = data.get("satis_kanali_id")
        csv_text = data.get("csv")
        rows_raw = data.get("rows")

        try:
            if not kanal_id:
                raise DjangoValidationError("satis_kanali_id zorunlu.")
            kanal = SatisKanali.objects.filter(pk=kanal_id).first()
            if kanal is None:
                raise DjangoValidationError("satis_kanali bulunamadı.")

            rows = None
            if rows_raw is not None:
                if not isinstance(rows_raw, list):
                    raise DjangoValidationError("rows liste olmalı.")
                rows = []
                for i, item in enumerate(rows_raw, start=1):
                    if not isinstance(item, dict):
                        raise DjangoValidationError(f"rows[{i}] nesne olmalı.")
                    try:
                        miktar = Decimal(str(item.get("miktar", "")))
                    except (InvalidOperation, TypeError) as exc:
                        raise DjangoValidationError(
                            f"rows[{i}].miktar geçersiz."
                        ) from exc
                    rows.append(
                        bulk_servisi.BulkRowInput(
                            satir_no=i,
                            sku=str(item.get("sku") or "").strip(),
                            miktar=miktar,
                            birim=(str(item["birim"]).strip() if item.get("birim") else None),
                        )
                    )

            result = bulk_servisi.toplu_siparis(
                actor=request.user,
                satis_kanali=kanal,
                idempotency_key=key,
                rows=rows,
                csv_text=None if rows is not None else csv_text,
            )
        except DjangoValidationError as exc:
            messages = getattr(exc, "messages", None) or [str(exc)]
            response = Response(
                {"detail": messages[0] if len(messages) == 1 else messages},
                status=status.HTTP_400_BAD_REQUEST,
            )
            return self.idempotency_commit(request, response)
        except ValidationError as exc:
            response = Response(
                exc.detail if hasattr(exc, "detail") else {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
            return self.idempotency_commit(request, response)

        body = {
            "order_id": result.order.pk if result.order else None,
            "replayed": result.replayed,
            "accepted": [
                {
                    "satir_no": a.satir_no,
                    "sku": a.sku,
                    "miktar": str(a.miktar),
                    "birim": a.birim,
                }
                for a in result.accepted
            ],
            "errors": [
                {"satir_no": e.satir_no, "sku": e.sku, "hata": e.hata}
                for e in result.errors
            ],
        }
        code = (
            status.HTTP_200_OK
            if result.replayed
            else (
                status.HTTP_201_CREATED
                if result.order is not None
                else status.HTTP_400_BAD_REQUEST
            )
        )
        response = Response(body, status=code)
        return self.idempotency_commit(request, response)
