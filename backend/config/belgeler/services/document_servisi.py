"""F6-012 — Document + taş sertifika bağı (storage binary yok)."""

from __future__ import annotations

from django.core.exceptions import PermissionDenied, ValidationError

from firmalar.role_permissions import P
from firmalar.services.audit_servisi import (
    domain_atomic,
    record_audit,
    record_audit_durable,
)
from firmalar.services.yetki_servisi import require_perm
from belgeler.models import Document, TasSertifikaBelgesi
from fiyatlama.models import TeklifTasMaliyeti
from urunler.models import UrunTasi


def _require_manage(actor, *, action: str, entity_id: str = ""):
    try:
        require_perm(
            actor,
            P["manage_document"],
            message="Belge için manage_document gerekir.",
        )
    except PermissionDenied:
        record_audit_durable(
            actor=actor,
            action=action,
            entity_type="Document",
            entity_id=entity_id,
            success=False,
            reason="yetki_yok",
        )
        raise


def olustur_tas_sertifika(
    *,
    actor,
    firma,
    baslik: str,
    storage_key: str,
    urun_tasi: UrunTasi | None = None,
    teklif_tas: TeklifTasMaliyeti | None = None,
    content_type: str = "",
    byte_size: int | None = None,
    metadata: dict | None = None,
) -> TasSertifikaBelgesi:
    """Document + TasSertifikaBelgesi atomik oluşturur."""
    _require_manage(actor, action="belgeler.document.create_denied")
    if (urun_tasi is None) == (teklif_tas is None):
        raise ValidationError("urun_tasi veya teklif_tas (tam biri) zorunlu.")
    if teklif_tas is not None:
        # Tedarikçi belgesi: firma teklif sahibi ile uyumlu olmalı
        ted_id = teklif_tas.teklif.tedarikci_id
        if firma.pk != ted_id:
            raise ValidationError(
                {"firma": "Teklif taş belgesi tedarikçi firmasına ait olmalı."}
            )
    storage_key = (storage_key or "").strip()
    baslik = (baslik or "").strip()
    if not storage_key or not baslik:
        raise ValidationError("baslik ve storage_key zorunlu.")

    with domain_atomic():
        doc = Document(
            firma=firma,
            tip=Document.Tip.TAS_SERTIFIKA,
            baslik=baslik[:120],
            storage_key=storage_key[:255],
            content_type=(content_type or "")[:64],
            byte_size=byte_size,
            metadata=metadata or {},
            olusturan=actor if getattr(actor, "pk", None) else None,
        )
        doc.save()
        bag = TasSertifikaBelgesi(
            document=doc,
            urun_tasi=urun_tasi,
            teklif_tas=teklif_tas,
        )
        bag.save()
        record_audit(
            actor=actor,
            action="belgeler.tas_sertifika.created",
            entity_type="TasSertifikaBelgesi",
            entity_id=str(bag.pk),
            success=True,
            detail={
                "document_id": doc.pk,
                "firma_id": firma.pk,
                "urun_tasi_id": urun_tasi.pk if urun_tasi else None,
                "teklif_tas_id": teklif_tas.pk if teklif_tas else None,
            },
        )
        return bag


def present_document(doc: Document) -> dict:
    """Maskeli özet — maliyet/tedarikçi kimliği yok (storage_key tenant’a)."""
    return {
        "id": doc.pk,
        "tip": doc.tip,
        "baslik": doc.baslik,
        "storage_key": doc.storage_key,
        "content_type": doc.content_type or "",
        "byte_size": doc.byte_size,
        "olusturma_tarihi": doc.olusturma_tarihi.isoformat()
        if doc.olusturma_tarihi
        else None,
    }
