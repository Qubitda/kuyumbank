"""DRF yüzeyi — Django ValidationError/PermissionDenied → problem+json."""

from __future__ import annotations

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError


def raise_drf(exc: BaseException) -> None:
    if isinstance(exc, DjangoPermissionDenied):
        raise PermissionDenied(detail=str(exc)) from exc
    if isinstance(exc, DjangoValidationError):
        if hasattr(exc, "message_dict") and exc.message_dict:
            raise ValidationError(detail=exc.message_dict) from exc
        msgs = getattr(exc, "messages", None) or [str(exc)]
        raise ValidationError(detail=msgs[0] if len(msgs) == 1 else list(msgs)) from exc
    raise exc


def not_found(msg: str = "Bulunamadı.") -> NotFound:
    return NotFound(detail=msg)
