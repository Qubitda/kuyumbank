#!/usr/bin/env python3
"""API-B1 — OpenAPI şemasını üret / drift kontrol et.

TECH-OPENAPI-01: SchemaGenerator relative `api.urls` patterns + url=/api/v1/
kullanır (ROOT_URLCONF ile çift önek oluşmaz). Canlı URL'ler değişmez.

Kullanım:
  python scripts/export_openapi.py           # docs/api/openapi-v1.json yazar
  python scripts/export_openapi.py --check   # commit'li dosya ile karşılaştır (CI)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend" / "config"
SCHEMA_PATH = ROOT / "docs" / "api" / "openapi-v1.json"


def _setup_django() -> None:
    sys.path.insert(0, str(BACKEND))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    import django

    django.setup()


def generate_schema() -> dict:
    from rest_framework.schemas.openapi import SchemaGenerator

    from api.urls import api_urlpatterns

    generator = SchemaGenerator(
        title="Kuyumbank API",
        description="API v1 — ADR-0017",
        version="1.0.0",
        url="/api/v1/",
        patterns=api_urlpatterns,
    )
    schema = generator.get_schema(request=None, public=True)
    if schema is None:
        raise SystemExit("OpenAPI şeması üretilemedi.")
    return schema


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="Commit'li şema ile üretileni karşılaştır; fark varsa exit 1",
    )
    args = parser.parse_args()
    _setup_django()
    schema = generate_schema()
    text = json.dumps(schema, indent=2, ensure_ascii=False, sort_keys=True) + "\n"

    if args.check:
        if not SCHEMA_PATH.is_file():
            print(f"Eksik şema dosyası: {SCHEMA_PATH}", file=sys.stderr)
            return 1
        existing = SCHEMA_PATH.read_text(encoding="utf-8")
        try:
            existing_norm = (
                json.dumps(
                    json.loads(existing), indent=2, ensure_ascii=False, sort_keys=True
                )
                + "\n"
            )
        except json.JSONDecodeError as exc:
            print(f"Geçersiz JSON: {SCHEMA_PATH}: {exc}", file=sys.stderr)
            return 1
        if existing_norm != text:
            print(
                "OpenAPI drift: docs/api/openapi-v1.json güncel değil. "
                "Çalıştır: python scripts/export_openapi.py",
                file=sys.stderr,
            )
            return 1
        print("OpenAPI schema OK (no drift).")
        return 0

    SCHEMA_PATH.parent.mkdir(parents=True, exist_ok=True)
    SCHEMA_PATH.write_text(text, encoding="utf-8")
    print(f"Wrote {SCHEMA_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
