#!/usr/bin/env python3
"""Kuyumbank docs AUTO blokları + kırık markdown link kontrolü.

Kullanım:
  python scripts/docs_sync.py          # MASTER.md AUTO bloklarını günceller
  python scripts/docs_sync.py --check  # değişiklik gerekirse exit 1
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "docs" / "MASTER.md"
DATA_DICTIONARY = ROOT / "docs" / "DATA_DICTIONARY.md"
BACKEND = ROOT / "backend" / "config"
APPS = (
    "api",
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


def _count_tests() -> dict[str, int]:
    counts: dict[str, int] = {}
    total = 0
    for app in APPS:
        n = 0
        tests_root = BACKEND / app / "tests"
        if tests_root.is_dir():
            for py in tests_root.rglob("test_*.py"):
                text = py.read_text(encoding="utf-8", errors="ignore")
                n += len(re.findall(r"^\s*def test_", text, flags=re.M))
        counts[app] = n
        total += n
    counts["_total"] = total
    return counts


def _migrations() -> list[tuple[str, int, str]]:
    rows = []
    for app in APPS:
        mig_dir = BACKEND / app / "migrations"
        files = sorted(
            p.name
            for p in mig_dir.glob("0*.py")
            if p.is_file() and p.name != "__init__.py"
        )
        last = files[-1].replace(".py", "") if files else "—"
        rows.append((app, len(files), last))
    return rows


def _api_urls() -> list[tuple[str, str]]:
    urls_py = BACKEND / "api" / "urls.py"
    text = urls_py.read_text(encoding="utf-8")
    out = []
    for m in re.finditer(
        r'path\(\s*"([^"]+)"\s*,\s*[^,]+,\s*name="([^"]+)"', text
    ):
        route, name = m.group(1), m.group(2)
        out.append((f"/api/v1/{route}", name))
    return out


def _commands() -> list[tuple[str, str, str]]:
    rows = []
    for app in APPS:
        cmd_dir = BACKEND / app / "management" / "commands"
        if not cmd_dir.is_dir():
            continue
        for py in sorted(cmd_dir.glob("*.py")):
            if py.name.startswith("_"):
                continue
            name = py.stem
            doc = ""
            text = py.read_text(encoding="utf-8", errors="ignore")
            m = re.search(r'help\s*=\s*["\']([^"\']+)["\']', text)
            if m:
                doc = m.group(1)
            else:
                dm = re.search(r'"""(.*?)"""', text, flags=re.S)
                if dm:
                    doc = " ".join(dm.group(1).strip().split())[:120]
            rows.append((name, app, doc or "—"))
    return rows


def _installed_apps_snippet() -> str:
    settings = BACKEND / "config" / "settings.py"
    text = settings.read_text(encoding="utf-8")
    m = re.search(r"INSTALLED_APPS\s*=\s*\[(.*?)\]", text, flags=re.S)
    if not m:
        return "`INSTALLED_APPS` okunamadı"
    raw = m.group(1)
    names = re.findall(r"['\"]([^'\"]+)['\"]", raw)
    short = []
    for n in names:
        if n.startswith("django.contrib."):
            continue
        short.append(n.split(".")[0] if ".apps." in n or n.endswith("Config") else n)
    # Config class paths → app label
    cleaned = []
    for n in names:
        if "django.contrib" in n:
            continue
        if n.endswith("Config"):
            # firmalar.apps.FirmalarConfig → firmalar
            cleaned.append(n.split(".")[0])
        else:
            cleaned.append(n)
    # unique preserve order
    seen = set()
    uniq = []
    for c in cleaned:
        if c not in seen:
            seen.add(c)
            uniq.append(c)
    contrib = sum(1 for n in names if n.startswith("django.contrib."))
    return (
        f"`INSTALLED_APPS` (koddan): `django.contrib.*` ({contrib}), "
        + ", ".join(f"`{u}`" for u in uniq)
    )


def _replace_auto_block(text: str, name: str, body: str) -> str:
    pattern = re.compile(
        rf"(<!-- AUTO:{name} -->\n)(.*?)(<!-- /AUTO:{name} -->)",
        flags=re.S,
    )
    repl = rf"\1{body.rstrip()}\n\3"
    new, n = pattern.subn(repl, text, count=1)
    if n != 1:
        raise SystemExit(f"AUTO:{name} bloğu bulunamadı veya birden fazla")
    return new


def render_master(text: str) -> str:
    counts = _count_tests()
    parts = " · ".join(f"`{a}` {counts[a]}" for a in APPS)
    tests_body = (
        f"Statik test sayısı (`def test_`): **{counts['_total']}** — {parts}\n"
        "_Bu sayı koşu sonucu değildir; son suite koşusu aşağıda elle tutulur._"
    )
    text = _replace_auto_block(text, "tests", tests_body)

    mig_lines = ["| App | Migration sayısı | Son migration |", "|-----|-----------------|---------------|"]
    for app, n, last in _migrations():
        mig_lines.append(f"| `{app}` | {n} | `{last}` |")
    text = _replace_auto_block(text, "migrations", "\n".join(mig_lines))

    url_lines = ["| Yol | Ad |", "|-----|----|"]
    for path, name in _api_urls():
        url_lines.append(f"| `{path}` | `{name}` |")
    text = _replace_auto_block(text, "api_urls", "\n".join(url_lines))

    cmd_lines = ["| Komut | Açıklama |", "|-------|----------|"]
    for name, app, doc in _commands():
        cmd_lines.append(f"| `manage.py {name}` ({app}) | {doc} |")
    text = _replace_auto_block(text, "commands", "\n".join(cmd_lines))

    if "<!-- AUTO:apps -->" in text:
        text = _replace_auto_block(text, "apps", _installed_apps_snippet())
    return text


def check_md_links() -> list[str]:
    """docs/ içi göreli .md linklerini doğrula."""
    errors: list[str] = []
    docs = ROOT / "docs"
    link_re = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
    for md in docs.rglob("*.md"):
        rel = md.relative_to(ROOT)
        for m in link_re.finditer(md.read_text(encoding="utf-8", errors="ignore")):
            target = m.group(2).split("#", 1)[0].strip()
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            if target.startswith("/"):
                continue
            resolved = (md.parent / target).resolve()
            try:
                resolved.relative_to(ROOT.resolve())
            except ValueError:
                errors.append(f"{rel}: dışarı kaçan link {target}")
                continue
            if not resolved.exists():
                errors.append(f"{rel}: kırık link → {target}")
    return errors


def _render_data_dictionary() -> str:
    """Django model meta → DATA_DICTIONARY.md (ayrı süreç: Django setup)."""
    import subprocess

    gen = ROOT / "scripts" / "gen_data_dictionary.py"
    proc = subprocess.run(
        [sys.executable, str(gen)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if proc.returncode != 0:
        raise SystemExit(
            f"DATA_DICTIONARY üretimi başarısız:\n{proc.stderr or proc.stdout}"
        )
    return proc.stdout


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Dosyayı yazma; AUTO drift veya kırık link varsa exit 1",
    )
    args = parser.parse_args()

    if not MASTER.is_file():
        print(f"MASTER yok: {MASTER}", file=sys.stderr)
        return 2

    original = MASTER.read_text(encoding="utf-8")
    updated = render_master(original)
    dict_body = _render_data_dictionary()
    dict_original = (
        DATA_DICTIONARY.read_text(encoding="utf-8")
        if DATA_DICTIONARY.is_file()
        else ""
    )
    link_errors = check_md_links()

    if args.check:
        drift = original != updated or dict_original != dict_body
        if original != updated:
            print("docs_sync --check: MASTER.md AUTO blokları bayat", file=sys.stderr)
        if dict_original != dict_body:
            print("docs_sync --check: DATA_DICTIONARY.md bayat", file=sys.stderr)
        for err in link_errors:
            print(err, file=sys.stderr)
        if drift or link_errors:
            return 1
        print("docs_sync --check: OK")
        return 0

    if updated != original:
        MASTER.write_text(updated, encoding="utf-8", newline="\n")
        print(f"Güncellendi: {MASTER.relative_to(ROOT)}")
    else:
        print("MASTER.md AUTO blokları zaten güncel")

    if dict_body != dict_original:
        DATA_DICTIONARY.write_text(dict_body, encoding="utf-8", newline="\n")
        print(f"Güncellendi: {DATA_DICTIONARY.relative_to(ROOT)}")
    else:
        print("DATA_DICTIONARY.md zaten güncel")

    for err in link_errors:
        print(f"UYARI: {err}", file=sys.stderr)
    return 1 if link_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
