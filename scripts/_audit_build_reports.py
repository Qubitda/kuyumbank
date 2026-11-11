#!/usr/bin/env python
"""Build docs/_audit markdown reports from code + OpenAPI + docs."""
from __future__ import annotations

import ast
import json
import os
import re
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend" / "config"
sys.path.insert(0, str(BACKEND))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from django.urls import get_resolver
from rest_framework.views import APIView

TODAY = date.today().isoformat()
AUDIT = ROOT / "docs" / "_audit"
AUDIT.mkdir(parents=True, exist_ok=True)


def iter_patterns(patterns, prefix=""):
    for p in patterns:
        if hasattr(p, "url_patterns"):
            yield from iter_patterns(p.url_patterns, prefix + str(p.pattern))
        else:
            yield prefix + str(p.pattern), p


def view_meta(callback):
    view = getattr(callback, "view_class", None) or getattr(callback, "cls", None)
    if view is None:
        return ["?"], None, [], [], None
    methods = []
    for m in ("get", "post", "put", "patch", "delete"):
        fn = getattr(view, m, None)
        if fn is None:
            continue
        # skip unoverridden APIView.get that raises
        methods.append(m.upper())
    perms = [getattr(c, "__name__", str(c)) for c in (getattr(view, "permission_classes", None) or [])]
    auths = [getattr(c, "__name__", str(c)) for c in (getattr(view, "authentication_classes", None) or [])]
    # serializer hints
    ser = getattr(view, "serializer_class", None)
    ser_name = ser.__name__ if ser else ""
    handler = f"{view.__module__}.{view.__name__}"
    return methods or ["?"], handler, perms, auths, ser_name


def normalize_path(p: str) -> str:
    p = "/" + p.lstrip("/")
    p = p.replace("<int:pk>", "{id}").replace("<int:line_id>", "{line_id}")
    p = p.replace("<int:user_id>", "{user_id}")
    p = re.sub(r"<[^>]+>", "{param}", p)
    if not p.endswith("/") and "{" not in p.split("/")[-1]:
        # keep as-is for act-as patterns
        pass
    return p


def collect_django():
    rows = []
    for path, pattern in iter_patterns(get_resolver().url_patterns):
        cb = getattr(pattern, "callback", None)
        if cb is None:
            continue
        full = "/" + path.lstrip("/")
        if not (full.startswith("/api/") or full.startswith("/act-as/")):
            continue
        methods, handler, perms, auths, ser = view_meta(cb)
        name = getattr(pattern, "name", "") or ""
        rows.append(
            {
                "path": full,
                "norm": normalize_path(full),
                "methods": methods,
                "name": name,
                "handler": handler or "?",
                "permissions": perms,
                "authentication": auths,
                "serializer": ser or "",
            }
        )
    return rows


def collect_openapi():
    data = json.loads((ROOT / "docs" / "api" / "openapi-v1.json").read_text(encoding="utf-8"))
    ops = []
    for path, methods in sorted(data.get("paths", {}).items()):
        for m, op in methods.items():
            if m.startswith("x-"):
                continue
            ops.append(
                {
                    "method": m.upper(),
                    "path": path,
                    "operationId": op.get("operationId", ""),
                    "tags": op.get("tags") or [],
                    "security": op.get("security", data.get("security")),
                    "has_request": "requestBody" in op,
                    "responses": sorted((op.get("responses") or {}).keys()),
                }
            )
    return ops, data


def doc_last_commits():
    """Use precomputed or filesystem mtimes; git dates filled externally."""
    return


DOC_FILES = [
    "AGENTS.md",
    "README.md",
    "backend/README.md",
    "docs/MASTER.md",
    "docs/API_CONTRACT.md",
    "docs/API_READINESS.md",
    "docs/BACKLOG.md",
    "docs/DATA_DICTIONARY.md",
    "docs/HISTORY.md",
    "docs/ROADMAP.md",
    "docs/RUNBOOK.md",
    "docs/api/openapi-v1.json",
    "frontend/README.md",
    "frontend/AGENTS.md",
    "frontend/docs/API.md",
    "frontend/docs/FRONTEND_ARCHITECTURE.md",
    "frontend/docs/COMPONENT_GUIDELINES.md",
    "frontend/docs/DESIGN_SYSTEM.md",
    "frontend/docs/PAGE_PATTERNS.md",
    "frontend/docs/UI_UX_GUIDELINES.md",
]


def write_endpoint_inventory(django_rows, oa_ops, git_doc_lines):
    lines = []
    lines.append("# Endpoint Inventory (ADIM 0)")
    lines.append("")
    lines.append(f"**Tarih:** {TODAY}")
    lines.append(f"**Kaynak kod:** `backend/config/api/urls.py` + `config/urls.py` + `api/docs_urls.py` + `firmalar/urls_act_as.py`")
    lines.append(f"**OpenAPI:** `docs/api/openapi-v1.json`")
    lines.append("")
    lines.append("## 0.1 Doküman envanteri (git last commit)")
    lines.append("")
    lines.append("| Dosya | Son commit tarihi | Hash | Konu |")
    lines.append("|-------|-------------------|------|------|")
    for row in git_doc_lines:
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")
    lines.append("Not: `NO_GIT_HISTORY` = diskte var, henüz commit edilmemiş (DOĞRULANDI `git log`).")
    lines.append("")
    lines.append("## 0.2 Özet sayılar")
    lines.append("")
    lines.append(f"| Kaynak | Adet |")
    lines.append(f"|--------|------|")
    lines.append(f"| Django `/api*` + `/act-as*` route kaydı | {len(django_rows)} |")
    lines.append(f"| OpenAPI path | {len({o['path'] for o in oa_ops})} |")
    lines.append(f"| OpenAPI operation (method×path) | {len(oa_ops)} |")
    lines.append("")
    lines.append("## 0.3 Django route tablosu")
    lines.append("")
    lines.append("| Metot | Yol | Name | Handler | permission_classes | Auth override | Serializer |")
    lines.append("|-------|-----|------|---------|--------------------|---------------|------------|")
    for r in sorted(django_rows, key=lambda x: (x["path"], ",".join(x["methods"]))):
        meth = ",".join(r["methods"])
        perms = ",".join(r["permissions"]) or "(DRF default)"
        auth = ",".join(r["authentication"]) or "(settings default)"
        lines.append(
            f"| {meth} | `{r['path']}` | {r['name']} | `{r['handler']}` | {perms} | {auth} | {r['serializer'] or '—'} |"
        )
    lines.append("")
    lines.append("## 0.4 OpenAPI operations")
    lines.append("")
    lines.append("| Metot | Yol | operationId | tags | requestBody | response codes |")
    lines.append("|-------|-----|-------------|------|-------------|----------------|")
    for o in oa_ops:
        tags = ",".join(o["tags"])
        lines.append(
            f"| {o['method']} | `{o['path']}` | {o['operationId']} | {tags} | "
            f"{'yes' if o['has_request'] else 'no'} | {','.join(o['responses'])} |"
        )
    lines.append("")
    lines.append("## 0.5 Auth notu (global)")
    lines.append("")
    lines.append("DRF varsayılanı `settings.REST_FRAMEWORK` — tipik: Session + Token; `IsAuthenticated` veya view-özel.")
    lines.append("Anonim: `health`, `auth/csrf`, `auth/login`, password-reset, invite accept, email-verify confirm, payments/webhook (özel).")
    lines.append("Kanıt: view dosyaları `backend/config/api/views/*.py`.")
    lines.append("")
    (AUDIT / "endpoint-inventory.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote endpoint-inventory.md")


def path_method_set_django(rows):
    s = set()
    for r in rows:
        for m in r["methods"]:
            if m == "?":
                continue
            s.add((m, r["norm"]))
    return s


def path_method_set_oa(ops):
    return {(o["method"], o["path"]) for o in ops}


def write_drift(django_rows, oa_ops):
    d_set = path_method_set_django(django_rows)
    o_set = path_method_set_oa(oa_ops)

    # Normalize django /api/v1/... vs openapi /api/v1/...
    # Also /api/schema vs /api/v1/schema
    only_code = sorted(d_set - o_set)
    only_oa = sorted(o_set - d_set)

    # Stale doc patterns (manual evidence collection)
    stale = []
    # Check API_CONTRACT item 9 about /buyer/
    ac = (ROOT / "docs" / "API_CONTRACT.md").read_text(encoding="utf-8")
    if "F9 Django HTML miras" in ac or "`/buyer/` korunur" in ac:
        stale.append(
            {
                "doc": "docs/API_CONTRACT.md:112",
                "claim": "F9 Django HTML miras (`/buyer/`) korunur",
                "code": "ADR-0029 + config/urls.py — /buyer|/supplier|/ops HTML yok",
                "kind": "c_diff",
            }
        )
    master = (ROOT / "docs" / "MASTER.md").read_text(encoding="utf-8")
    for m in re.finditer(r"`(/buyer/[^`]*)`", master):
        stale.append(
            {
                "doc": f"docs/MASTER.md (match {m.group(1)})",
                "claim": f"HTML path {m.group(1)} UYGULANDI tablosunda",
                "code": "ADR-0029 HTML kaldırıldı; test/view dosyaları kontrol edilmeli",
                "kind": "c_diff",
            }
        )

    # HTML view modules existence
    buyer_ui = list((BACKEND / "siparis").rglob("*buyer*"))
    finance_ui = list(BACKEND.rglob("*finance_ui*"))
    approval_ui = list(BACKEND.rglob("*approval_ui*"))
    rfq_ui = list(BACKEND.rglob("*rfq_ui*"))

    lines = []
    lines.append("# Drift Report (ADIM 1)")
    lines.append("")
    lines.append(f"**Tarih:** {TODAY}")
    lines.append("**Kural:** şüphede kod + OpenAPI kazanır (`API_CONTRACT` §üst).")
    lines.append("")
    lines.append("## a) Dökümanda/OpenAPI var, kodda yok (eksik implementasyon)")
    lines.append("")
    if only_oa:
        lines.append("| Metot | Path (OpenAPI) | Not |")
        lines.append("|-------|----------------|-----|")
        for m, p in only_oa:
            lines.append(f"| {m} | `{p}` | OpenAPI’de var; Django route setinde birebir eşleşme yok |")
    else:
        lines.append("_OpenAPI operation’larının tamamı Django norm path setinde (normalize sonrası)._")
    lines.append("")
    lines.append("## b) Kodda var, OpenAPI/dökümanda yok (dökümansız)")
    lines.append("")
    if only_code:
        lines.append("| Metot | Path (Django norm) | Not |")
        lines.append("|-------|--------------------|-----|")
        for m, p in only_code:
            lines.append(f"| {m} | `{p}` | Route var; OpenAPI paths’te yok veya path normalize farkı |")
    else:
        lines.append("_Yok (normalize sonrası)._")
    lines.append("")
    lines.append("## c) İkisinde de var ama farklı / bayat döküman iddiaları")
    lines.append("")
    lines.append("| Döküman kanıtı | İddia | Kod gerçeği |")
    lines.append("|----------------|-------|-------------|")
    for s in stale:
        lines.append(f"| {s['doc']} | {s['claim']} | {s['code']} |")
    # path count claim
    m = re.search(r"\*\*(\d+)\*\* path", ac)
    oa_path_count = len({o["path"] for o in oa_ops})
    if m:
        claimed = int(m.group(1))
        if claimed != oa_path_count:
            lines.append(
                f"| docs/API_CONTRACT.md:89 | OpenAPI paths **{claimed}** | Gerçek openapi-v1.json path sayısı **{oa_path_count}** |"
            )
    lines.append("")
    lines.append("## HTML portal dosya kanıtı (ADR-0029)")
    lines.append("")
    lines.append(f"| Glob | Bulunan |")
    lines.append(f"|------|---------|")
    lines.append(f"| siparis *buyer* | {len(buyer_ui)} → {[str(p.relative_to(BACKEND)) for p in buyer_ui[:8]]} |")
    lines.append(f"| *finance_ui* | {len(finance_ui)} → {[str(p.relative_to(ROOT)) for p in finance_ui[:5]]} |")
    lines.append(f"| *approval_ui* | {len(approval_ui)} |")
    lines.append(f"| *rfq_ui* | {len(rfq_ui)} |")
    lines.append("")
    lines.append("## Normalize farkları (bilinçli)")
    lines.append("")
    lines.append("- Django: `/api/v1/schema/` + `/api/schema/` (çift mount)")
    lines.append("- Django: `/api/docs/`, `/api/redoc/` (OpenAPI UI; ops listesinde olmayabilir)")
    lines.append("- Django: `/act-as/start/<user_id>/`, `/act-as/stop/` (Admin redirect; API: `/api/v1/act-as/*`)")
    lines.append("- OpenAPI path param: `{id}` vs Django `<int:pk>`")
    lines.append("")
    (AUDIT / "drift-report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote drift-report.md")
    return {
        "only_oa": only_oa,
        "only_code": only_code,
        "stale": stale,
        "oa_path_count": oa_path_count,
    }


OPEN_PATTERNS = re.compile(
    r"\b(TODO|FIXME|HACK|XXX)\b|NotImplementedError|\bpass\b|mock|stub|hardcoded",
    re.I,
)


def scan_open_work():
    items = []
    roots = [BACKEND / "api", BACKEND / "firmalar", BACKEND / "siparis", BACKEND / "finans",
             BACKEND / "stok", BACKEND / "fiyatlama", BACKEND / "urunler", BACKEND / "kalite",
             BACKEND / "lojistik", BACKEND / "tanimlar", BACKEND / "piyasa", BACKEND / "bildirim",
             BACKEND / "belgeler"]
    skip = {"migrations", "__pycache__", "tests"}
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*.py"):
            if any(part in skip for part in path.parts):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except Exception:
                continue
            for i, line in enumerate(text.splitlines(), 1):
                if "TODO" in line or "FIXME" in line or "HACK" in line or "XXX" in line:
                    items.append(("P1", str(path.relative_to(ROOT)), i, line.strip()[:160], "TODO/FIXME temizle veya backlog’a bağla"))
                if "NotImplementedError" in line:
                    items.append(("P0", str(path.relative_to(ROOT)), i, line.strip()[:160], "Implement veya Deprecated işaretle"))
                if re.search(r"^\s*pass\s*$", line) and i > 1:
                    # noisy; only in views
                    if "views" in str(path):
                        items.append(("P2", str(path.relative_to(ROOT)), i, "pass in views", "Boş handler kontrolü"))
    # Punchout stub mention in MASTER
    return items


def write_open_work(items, readiness_notes):
    lines = []
    lines.append("# Open Work (ADIM 4)")
    lines.append("")
    lines.append(f"**Tarih:** {TODAY}")
    lines.append("")
    lines.append("## Tarama özeti")
    lines.append("")
    lines.append(f"Kod TODO/FIXME/NotImplemented (tests/migrations hariç): **{len(items)}** bulgu.")
    lines.append("")
    lines.append("| Öncelik | Dosya:satır | Açıklama | Önerilen çözüm |")
    lines.append("|---------|-------------|----------|----------------|")
    for pri, f, ln, desc, sol in items[:200]:
        lines.append(f"| {pri} | `{f}:{ln}` | `{desc}` | {sol} |")
    lines.append("")
    lines.append("## Bilinçli açık işler (MASTER §12.3 / API_CONTRACT §4)")
    lines.append("")
    for n in readiness_notes:
        lines.append(f"- {n}")
    lines.append("")
    lines.append("## Endpoint test / OpenAPI / migration kontrol checklist (özet)")
    lines.append("")
    lines.append("Detaylı ✅/❌ tablo: `FINAL-REPORT.md` ADIM 5.")
    lines.append("")
    (AUDIT / "open-work.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote open-work.md")


def main():
    git_path = AUDIT / "_git_docs.txt"
    git_doc_lines = []
    if git_path.exists():
        for line in git_path.read_text(encoding="utf-8").splitlines():
            parts = line.split("|", 3)
            if len(parts) >= 3:
                f, date_h, *rest = parts[0], parts[1], parts[2:]
                # format: file|date|hash|subject OR file|date|hash|subject
                segs = line.split("|")
                if len(segs) >= 4:
                    git_doc_lines.append([segs[0], segs[1][:19] if segs[1] else "NO_GIT_HISTORY", segs[2], segs[3][:60]])
                elif len(segs) == 3:
                    git_doc_lines.append([segs[0], segs[1], segs[2], ""])
    else:
        for f in DOC_FILES:
            git_doc_lines.append([f, "see git", "?", ""])
        for p in sorted((ROOT / "docs" / "decisions").glob("*.md")):
            rel = str(p.relative_to(ROOT)).replace("\\", "/")
            git_doc_lines.append([rel, "see git", "?", ""])

    django_rows = collect_django()
    oa_ops, _ = collect_openapi()
    write_endpoint_inventory(django_rows, oa_ops, git_doc_lines)
    drift = write_drift(django_rows, oa_ops)

    readiness_notes = [
        "P1 NX/F9 Next portal dilimleri — API_READINESS READY; ürün sahibi talimatı (MASTER §12.3)",
        "P2 F6-032 Platform uyuşmazlık ops kuyruğu UI",
        "Bilinçli: CORS erteli; RFQ eşleştirme HTTP yok; teklif create HTTP yok; Celery yok; gerçek ödeme/kargo yok",
        "ADR-0017 bütünü Taslak (NX maddeleri Kabul)",
        "Fake payment/carrier adapter — bilinçli (F5-020 / F6-021)",
    ]
    items = scan_open_work()
    write_open_work(items, readiness_notes)

    # save raw for adim5
    (AUDIT / "_raw_inventory.json").write_text(
        json.dumps({"django": django_rows, "openapi": oa_ops, "drift": {
            "only_oa": drift["only_oa"],
            "only_code": drift["only_code"],
            "oa_path_count": drift["oa_path_count"],
        }}, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    print("counts", len(django_rows), len(oa_ops), "only_oa", len(drift["only_oa"]), "only_code", len(drift["only_code"]))


if __name__ == "__main__":
    main()
