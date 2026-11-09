"""DATA_DICTIONARY.md üretici — docs_sync tarafından çağrılır."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend" / "config"
sys.path.insert(0, str(BACKEND))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from django.apps import apps
from django.db import models

DOMAIN_APPS = (
    "firmalar",
    "fiyatlama",
    "finans",
    "kalite",
    "lojistik",
    "belgeler",
    "siparis",
    "stok",
    "tanimlar",
    "urunler",
)


def _field_type(field) -> str:
    return field.get_internal_type()


def _field_target(field) -> str:
    if isinstance(field, (models.ForeignKey, models.OneToOneField)):
        rel = field.remote_field.model
        if isinstance(rel, str):
            target = rel
        else:
            target = f"{rel._meta.app_label}.{rel.__name__}"
        on_delete = field.remote_field.on_delete.__name__
        return f"{target} ({on_delete})"
    if isinstance(field, models.ManyToManyField):
        rel = field.remote_field.model
        if isinstance(rel, str):
            return rel
        return f"{rel._meta.app_label}.{rel.__name__}"
    if isinstance(field, models.CharField):
        bits = [f"max {field.max_length}"]
        if field.choices:
            bits.append("choices")
        return ", ".join(bits)
    if isinstance(field, models.DecimalField):
        return f"{field.max_digits},{field.decimal_places}"
    return ""


def _field_flags(field) -> str:
    flags = []
    if field.null:
        flags.append("null")
    if getattr(field, "unique", False):
        flags.append("benzersiz")
    if field.blank and not field.null:
        flags.append("blank")
    return ", ".join(flags)


def _help(field) -> str:
    ht = (field.help_text or "").strip().replace("\n", " ")
    if len(ht) > 100:
        return ht[:97] + "..."
    return ht


def render() -> str:
    lines = [
        "# Kuyumbank — Veri sözlüğü",
        "",
        "> **Otomatik üretilir** (`python scripts/docs_sync.py`). Elle düzenlemeyin; "
        "açıklama için modeldeki `help_text` / docstring güncellenir.",
        "> Kaynak: Django model meta. Migration / DB şema için kod/DB kazanır.",
        "",
    ]
    for app_label in DOMAIN_APPS:
        try:
            app_config = apps.get_app_config(app_label)
        except LookupError:
            continue
        lines.append(f"## `{app_label}`")
        lines.append("")
        for model in sorted(app_config.get_models(), key=lambda m: m.__name__):
            if model._meta.proxy:
                continue
            lines.append(f"### {model.__name__}")
            lines.append("")
            doc = (model.__doc__ or "").strip().split("\n")[0].strip()
            if doc:
                lines.append(doc)
                lines.append("")
            lines.append("| Alan | Tip | Hedef / boyut | Bayrak | Not |")
            lines.append("|------|-----|---------------|--------|-----|")
            for field in model._meta.local_fields + list(
                model._meta.local_many_to_many
            ):
                if field.auto_created and not field.concrete:
                    continue
                if field.name == "id" and field.primary_key:
                    continue
                lines.append(
                    f"| `{field.name}` | {_field_type(field)} | "
                    f"{_field_target(field)} | {_field_flags(field)} | {_help(field)} |"
                )
            constraints = [
                f"`{c.name}` ({c.__class__.__name__})"
                for c in model._meta.constraints
            ]
            if constraints:
                lines.append("")
                lines.append("**Kısıtlar:** " + "; ".join(constraints))
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    sys.stdout.write(render())
