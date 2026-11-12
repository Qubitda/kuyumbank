"""GAP-F3-04 — Tedarikçi föy CSV preview → commit (taslak teklifler).

PDF bu dilimde desteklenmez (açık 400). Marj/alıcı bilgisi yok.
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from firmalar.role_permissions import P
from firmalar.services.yetki_servisi import require_perm
from fiyatlama.models import TedarikciTeklif
from fiyatlama.services import teklif_servisi
from urunler.models import Varyant

MAX_ROWS = 500

_FIYAT_ALIAS = {
    "METAL_BAZLI": TedarikciTeklif.FiyatModeli.METAL_BAZLI,
    "METAL": TedarikciTeklif.FiyatModeli.METAL_BAZLI,
    "GRAM_BIRIM": TedarikciTeklif.FiyatModeli.GRAM_BIRIM,
    "GRAM": TedarikciTeklif.FiyatModeli.GRAM_BIRIM,
    "SABIT_PARCA": TedarikciTeklif.FiyatModeli.SABIT_PARCA,
    "ADET": TedarikciTeklif.FiyatModeli.SABIT_PARCA,
    "PARCA": TedarikciTeklif.FiyatModeli.SABIT_PARCA,
}


@dataclass
class ImportHata:
    satir_no: int
    hata: str


@dataclass
class ImportSatir:
    satir_no: int
    varyant_id: int
    fiyat_modeli: str
    birim_fiyat: str | None = None
    gram: str | None = None
    iscilik_override: str | None = None
    para_birimi: str = "TRY"
    tedarikci_kodu: str = ""
    sku: str = ""


@dataclass
class PreviewResult:
    satirlar: list[ImportSatir] = field(default_factory=list)
    hatalar: list[ImportHata] = field(default_factory=list)
    server_now: str = ""


@dataclass
class CommitResult:
    created: list[dict[str, Any]] = field(default_factory=list)
    hatalar: list[ImportHata] = field(default_factory=list)
    server_now: str = ""


def _require_supplier_manage(actor) -> None:
    firma = getattr(actor, "firma", None)
    if firma is None or not getattr(firma, "tedarikci_mi", False):
        raise PermissionDenied("Föy import yalnız tedarikçi firması.")
    require_perm(
        actor,
        P["manage_own_teklif"],
        message="Teklif yönetim yetkiniz yok.",
    )


def _norm_header(name: str | None) -> str:
    return (name or "").strip().lower().replace(" ", "_")


def _dec_or_none(raw: str | None, *, field: str, satir_no: int) -> Decimal | None:
    if raw is None or str(raw).strip() == "":
        return None
    try:
        return Decimal(str(raw).strip().replace(",", "."))
    except (InvalidOperation, TypeError) as exc:
        raise ValidationError(f"satır {satir_no}: {field} geçersiz.") from exc


def _map_fiyat_modeli(raw: str) -> str:
    key = (raw or "").strip().upper()
    if key not in _FIYAT_ALIAS:
        raise ValidationError(
            f"fiyat_modeli geçersiz: {raw!r} "
            f"(METAL_BAZLI|GRAM_BIRIM|SABIT_PARCA)."
        )
    return _FIYAT_ALIAS[key]


def _resolve_varyant(
    *,
    varyant_id: int | None,
    sku: str,
    satir_no: int,
) -> Varyant:
    if varyant_id is not None:
        v = Varyant.objects.filter(pk=varyant_id, aktif=True).first()
        if v is None:
            raise ValidationError(f"satır {satir_no}: aktif varyant_id bulunamadı.")
        return v
    if sku:
        v = Varyant.objects.filter(sku=sku, aktif=True).first()
        if v is None:
            raise ValidationError(f"satır {satir_no}: aktif sku bulunamadı: {sku!r}.")
        return v
    raise ValidationError(f"satır {satir_no}: varyant_id veya sku zorunlu.")


def assert_not_pdf(*, filename: str | None = None, content_type: str | None = None) -> None:
    name = (filename or "").lower()
    ctype = (content_type or "").lower()
    if name.endswith(".pdf") or "pdf" in ctype:
        raise ValidationError(
            "PDF föy henüz desteklenmiyor; CSV yükleyin (GAP-F3-04 CSV-önce)."
        )


def parse_csv_text(text: str) -> list[dict[str, str]]:
    """Ham CSV → satır dict listesi (başlık normalize)."""
    if text is None or not str(text).strip():
        raise ValidationError("CSV boş.")
    reader = csv.DictReader(io.StringIO(str(text).lstrip("\ufeff")))
    if not reader.fieldnames:
        raise ValidationError("CSV başlık satırı yok.")
    fields = {_norm_header(f): (f or "") for f in reader.fieldnames}
    # zorunlu sütun grubu
    has_varyant = "varyant_id" in fields or "sku" in fields
    if not has_varyant or "fiyat_modeli" not in fields:
        raise ValidationError(
            "CSV sütunları zorunlu: fiyat_modeli + (varyant_id veya sku); "
            "opsiyonel: birim_fiyat, gram, iscilik_override, para_birimi, tedarikci_kodu."
        )
    out: list[dict[str, str]] = []
    for i, raw in enumerate(reader, start=2):
        row = {k: (raw.get(orig) or "").strip() for k, orig in fields.items()}
        if not any(row.values()):
            continue
        row["_satir_no"] = str(i)
        out.append(row)
    if not out:
        raise ValidationError("CSV'de işlenecek satır yok.")
    if len(out) > MAX_ROWS:
        raise ValidationError(f"En fazla {MAX_ROWS} satır desteklenir.")
    return out


def _normalize_row(raw: dict[str, str]) -> ImportSatir:
    satir_no = int(raw.get("_satir_no") or raw.get("satir_no") or 0)
    vid_raw = (raw.get("varyant_id") or "").strip()
    sku = (raw.get("sku") or "").strip()
    varyant_id = None
    if vid_raw:
        try:
            varyant_id = int(vid_raw)
        except ValueError as exc:
            raise ValidationError(f"satır {satir_no}: varyant_id tam sayı olmalı.") from exc

    fiyat_modeli = _map_fiyat_modeli(raw.get("fiyat_modeli") or "")
    varyant = _resolve_varyant(varyant_id=varyant_id, sku=sku, satir_no=satir_no)

    birim = _dec_or_none(raw.get("birim_fiyat"), field="birim_fiyat", satir_no=satir_no)
    gram = _dec_or_none(raw.get("gram"), field="gram", satir_no=satir_no)
    iscilik = _dec_or_none(
        raw.get("iscilik_override"), field="iscilik_override", satir_no=satir_no
    )
    pb = (raw.get("para_birimi") or "TRY").strip().upper()[:3] or "TRY"
    kod = (raw.get("tedarikci_kodu") or "")[:64]

    # Alan zorunlulukları (DB check ile hizalı erken uyarı)
    if fiyat_modeli == TedarikciTeklif.FiyatModeli.METAL_BAZLI and gram is None:
        raise ValidationError(f"satır {satir_no}: METAL_BAZLI için gram zorunlu.")
    if fiyat_modeli == TedarikciTeklif.FiyatModeli.GRAM_BIRIM and (
        gram is None or birim is None
    ):
        raise ValidationError(
            f"satır {satir_no}: GRAM_BIRIM için gram ve birim_fiyat zorunlu."
        )
    if fiyat_modeli == TedarikciTeklif.FiyatModeli.SABIT_PARCA and birim is None:
        raise ValidationError(f"satır {satir_no}: SABIT_PARCA için birim_fiyat zorunlu.")

    return ImportSatir(
        satir_no=satir_no,
        varyant_id=varyant.pk,
        sku=varyant.sku or sku,
        fiyat_modeli=fiyat_modeli,
        birim_fiyat=str(birim) if birim is not None else None,
        gram=str(gram) if gram is not None else None,
        iscilik_override=str(iscilik) if iscilik is not None else None,
        para_birimi=pb,
        tedarikci_kodu=kod,
    )


def preview_csv(actor, *, csv_text: str) -> PreviewResult:
    _require_supplier_manage(actor)
    raw_rows = parse_csv_text(csv_text)
    ok: list[ImportSatir] = []
    hatalar: list[ImportHata] = []
    for raw in raw_rows:
        satir_no = int(raw.get("_satir_no") or 0)
        try:
            ok.append(_normalize_row(raw))
        except ValidationError as exc:
            msg = "; ".join(getattr(exc, "messages", None) or [str(exc)])
            hatalar.append(ImportHata(satir_no=satir_no, hata=msg))
    return PreviewResult(
        satirlar=ok,
        hatalar=hatalar,
        server_now=timezone.now().isoformat(),
    )


def _satir_from_payload(item: dict, *, index: int) -> ImportSatir:
    if not isinstance(item, dict):
        raise ValidationError(f"satirlar[{index}] nesne olmalı.")
    satir_no = item.get("satir_no")
    try:
        satir_no_i = int(satir_no) if satir_no not in (None, "") else index
    except (TypeError, ValueError):
        satir_no_i = index
    raw = {
        "_satir_no": str(satir_no_i),
        "varyant_id": str(item.get("varyant_id") or ""),
        "sku": str(item.get("sku") or ""),
        "fiyat_modeli": str(item.get("fiyat_modeli") or ""),
        "birim_fiyat": str(item.get("birim_fiyat") or ""),
        "gram": str(item.get("gram") or ""),
        "iscilik_override": str(item.get("iscilik_override") or ""),
        "para_birimi": str(item.get("para_birimi") or "TRY"),
        "tedarikci_kodu": str(item.get("tedarikci_kodu") or ""),
    }
    return _normalize_row(raw)


def commit_rows(actor, *, satirlar: list[dict]) -> CommitResult:
    """Tüm satırlar geçerliyse atomic taslak oluştur; aksi  ValidationError (hiç yazma)."""
    _require_supplier_manage(actor)
    if not isinstance(satirlar, list) or not satirlar:
        raise ValidationError("satirlar zorunlu (boş olamaz).")
    if len(satirlar) > MAX_ROWS:
        raise ValidationError(f"En fazla {MAX_ROWS} satır desteklenir.")

    normalized: list[ImportSatir] = []
    hatalar: list[ImportHata] = []
    for i, item in enumerate(satirlar, start=1):
        try:
            normalized.append(_satir_from_payload(item, index=i))
        except ValidationError as exc:
            msg = "; ".join(getattr(exc, "messages", None) or [str(exc)])
            hatalar.append(ImportHata(satir_no=i, hata=msg))

    if hatalar:
        # Commit kapısı: hatalı satır varken yazma yok
        raise ValidationError(
            {
                "hatalar": [{"satir_no": h.satir_no, "hata": h.hata} for h in hatalar],
                "detail": "Commit reddedildi; satırları düzeltip yeniden deneyin.",
            }
        )

    created: list[dict[str, Any]] = []
    with transaction.atomic():
        for row in normalized:
            varyant = Varyant.objects.get(pk=row.varyant_id)
            teklif = teklif_servisi.taslak_olustur(
                actor,
                varyant=varyant,
                fiyat_modeli=row.fiyat_modeli,
                gram=Decimal(row.gram) if row.gram is not None else None,
                birim_fiyat=(
                    Decimal(row.birim_fiyat) if row.birim_fiyat is not None else None
                ),
                tedarikci_kodu=row.tedarikci_kodu,
                iscilik_override=(
                    Decimal(row.iscilik_override)
                    if row.iscilik_override is not None
                    else None
                ),
                para_birimi=row.para_birimi,
            )
            created.append(
                {
                    "satir_no": row.satir_no,
                    "teklif_id": teklif.pk,
                    "varyant_id": row.varyant_id,
                    "durum": teklif.durum,
                }
            )

    return CommitResult(
        created=created,
        hatalar=[],
        server_now=timezone.now().isoformat(),
    )


def satir_to_dict(s: ImportSatir) -> dict[str, Any]:
    return {
        "satir_no": s.satir_no,
        "varyant_id": s.varyant_id,
        "sku": s.sku,
        "fiyat_modeli": s.fiyat_modeli,
        "birim_fiyat": s.birim_fiyat,
        "gram": s.gram,
        "iscilik_override": s.iscilik_override,
        "para_birimi": s.para_birimi,
        "tedarikci_kodu": s.tedarikci_kodu,
    }
