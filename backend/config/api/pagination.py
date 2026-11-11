"""ADR-0017 NX-2 — tek liste zarfı (page + page_size); deterministik sıra."""

from __future__ import annotations

from typing import Any, Callable, Iterable

from django.core.paginator import EmptyPage, Paginator
from rest_framework.exceptions import NotFound
from rest_framework.request import Request
from rest_framework.response import Response

DEFAULT_PAGE_SIZE = 25
MAX_PAGE_SIZE = 100


def _int_param(request: Request, name: str, default: int) -> int:
    raw = request.query_params.get(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


def _with_pk_tiebreak(fields: list[str]) -> list[str]:
    """Eşit sıralama değerlerinde kararlı sayfa için ikincil -pk."""
    names = {(f[1:] if f.startswith("-") else f) for f in fields}
    if "pk" not in names and "id" not in names:
        fields = [*fields, "-pk"]
    return fields


def apply_ordering(qs, request: Request, *, whitelist: Iterable[str], default: str):
    """`ordering=` beyaz liste; `-alan` desteklenir; her zaman pk tie-break."""
    allowed = set(whitelist) | {"pk"}
    raw = (request.query_params.get("ordering") or "").strip() or default
    fields: list[str] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        name = part[1:] if part.startswith("-") else part
        if name not in allowed:
            continue
        fields.append(part)
    if not fields:
        fields = [default]
    fields = _with_pk_tiebreak(fields)
    return qs.order_by(*fields)


def build_page_urls(
    request: Request, *, page: int, page_size: int, num_pages: int
) -> tuple[str | None, str | None]:
    def _url(p: int) -> str:
        q = request.query_params.copy()
        q["page"] = str(p)
        q["page_size"] = str(page_size)
        return request.build_absolute_uri(f"{request.path}?{q.urlencode()}")

    next_url = _url(page + 1) if page < num_pages else None
    prev_url = _url(page - 1) if page > 1 else None
    return next_url, prev_url


def paginate_queryset(
    request: Request,
    qs,
    *,
    present: Callable[[Any], dict],
    extra: dict | None = None,
) -> Response:
    """QuerySet → standart liste zarfı."""
    page = max(1, _int_param(request, "page", 1))
    page_size = min(
        MAX_PAGE_SIZE, max(1, _int_param(request, "page_size", DEFAULT_PAGE_SIZE))
    )
    paginator = Paginator(qs, page_size)
    try:
        page_obj = paginator.page(page)
    except EmptyPage as exc:
        # Sessizce son sayfaya düşürme — istemci sonsuz döngü riski
        raise NotFound(detail="Sayfa bulunamadı.") from exc

    next_url, prev_url = build_page_urls(
        request, page=page, page_size=page_size, num_pages=paginator.num_pages
    )
    body: dict[str, Any] = {
        "count": paginator.count,
        "next": next_url,
        "previous": prev_url,
        "page": page,
        "page_size": page_size,
        "results": [present(obj) for obj in page_obj.object_list],
    }
    if extra:
        body.update(extra)
    return Response(body)


def paginate_sequence(
    request: Request,
    items: list[dict],
    *,
    extra: dict | None = None,
) -> Response:
    """Önceden materialize liste (küçük ops özetleri)."""
    page = max(1, _int_param(request, "page", 1))
    page_size = min(
        MAX_PAGE_SIZE, max(1, _int_param(request, "page_size", DEFAULT_PAGE_SIZE))
    )
    paginator = Paginator(items, page_size)
    try:
        page_obj = paginator.page(page)
    except EmptyPage as exc:
        raise NotFound(detail="Sayfa bulunamadı.") from exc
    next_url, prev_url = build_page_urls(
        request, page=page, page_size=page_size, num_pages=paginator.num_pages
    )
    body: dict[str, Any] = {
        "count": paginator.count,
        "next": next_url,
        "previous": prev_url,
        "page": page,
        "page_size": page_size,
        "results": list(page_obj.object_list),
    }
    if extra:
        body.update(extra)
    return Response(body)
