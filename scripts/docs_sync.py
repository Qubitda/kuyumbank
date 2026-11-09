#!/usr/bin/env python3
"""Kuyumbank docs AUTO blokları + kırık markdown link + docs lint.

Kullanım:
  python scripts/docs_sync.py                 # MASTER AUTO + DATA_DICTIONARY güncelle
  python scripts/docs_sync.py --check         # drift/link → exit 1; lint → UYARI (exit bozmaz)
  python scripts/docs_sync.py --lint-docs     # yalnız lint UYARI (exit 0)
  python scripts/docs_sync.py --lint-docs-strict  # lint ihlali → exit 1
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "docs" / "MASTER.md"
DATA_DICTIONARY = ROOT / "docs" / "DATA_DICTIONARY.md"
ROADMAP = ROOT / "docs" / "ROADMAP.md"
ADR_README = ROOT / "docs" / "decisions" / "README.md"
ADR_0017 = ROOT / "docs" / "decisions" / "ADR-0017-nextjs-api-sozlesmesi.md"
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

# Canlı (non-tarihsel) markdown — hash / bayat ifade taraması
_LIVE_MD = (
    MASTER,
    ROADMAP,
    ADR_README,
    ROOT / "docs" / "BACKLOG.md",
    ROOT / "docs" / "RUNBOOK.md",
)

_HASH_RE = re.compile(r"(?<![0-9a-fA-F/`])\b([0-9a-f]{7,40})\b(?![0-9a-fA-F])")
_FENCE_RE = re.compile(r"```.*?```", flags=re.S)
_INLINE_CODE_RE = re.compile(r"`[^`]+`")

# Bilinçli allowlist: teslimat etiketi / bilinen kısa hash
_HASH_ALLOW = frozenset(
    {
        "b529e5e",  # B1–B3 teslimat etiketi (tarihsel)
        "b529e5ecc030590e169707e2757a67e5c8a93633",
    }
)

_BANNED_PHRASES = (
    "B4 henüz başlatılmadı",
    "Sırada: B2",
    "Sırada:** B2",
    "**555 OK**",
)


def _git_ls_files(*patterns: str) -> set[Path]:
    """Repo köküne göre tracked dosya seti; git yoksa boş → caller disk’e düşer."""
    try:
        proc = subprocess.run(
            ["git", "ls-files", "-z", "--", *patterns],
            cwd=str(ROOT),
            capture_output=True,
            check=False,
        )
    except OSError:
        return set()
    if proc.returncode != 0:
        return set()
    out: set[Path] = set()
    for raw in proc.stdout.split(b"\0"):
        if not raw:
            continue
        out.add((ROOT / raw.decode("utf-8", errors="replace")).resolve())
    return out


def _count_tests() -> dict[str, int]:
    """Yalnız git-tracked test_*.py (WIP disk dosyaları sayıyı şişirmesin)."""
    tracked = _git_ls_files("backend/config/*/tests/**")
    use_git = bool(tracked)
    counts: dict[str, int] = {}
    total = 0
    for app in APPS:
        n = 0
        tests_root = BACKEND / app / "tests"
        if tests_root.is_dir():
            for py in tests_root.rglob("test_*.py"):
                if use_git and py.resolve() not in tracked:
                    continue
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
    cleaned = []
    for n in names:
        if "django.contrib" in n:
            continue
        if n.endswith("Config"):
            cleaned.append(n.split(".")[0])
        else:
            cleaned.append(n)
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
    note = (
        "_(git-tracked `test_*.py`; WIP untracked sayılmaz). "
        "Koşu sonucu değildir; son suite aşağıda elle._"
    )
    tests_body = (
        f"Statik test sayısı (`def test_`): **{counts['_total']}** — {parts}\n"
        f"{note}"
    )
    text = _replace_auto_block(text, "tests", tests_body)

    mig_lines = [
        "| App | Migration sayısı | Son migration |",
        "|-----|-----------------|---------------|",
    ]
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


def _strip_code(text: str) -> str:
    text = _FENCE_RE.sub("", text)
    text = _INLINE_CODE_RE.sub("", text)
    return text


def _lint_hashes(path: Path) -> list[str]:
    """Canlı docs’ta sabit commit hash yasak (HISTORY hariç; allowlist hariç)."""
    if path.name == "HISTORY.md":
        return []
    raw = path.read_text(encoding="utf-8", errors="ignore")
    scanned = _strip_code(raw)
    hits: list[str] = []
    rel = path.relative_to(ROOT)
    for m in _HASH_RE.finditer(scanned):
        h = m.group(1).lower()
        if h in _HASH_ALLOW:
            continue
        # Saf hex olmayan / çok kısa bağlam: zaten 7–40
        line_no = scanned[: m.start()].count("\n") + 1
        hits.append(f"{rel}:{line_no}: sabit commit hash `{h}` (git log kullan)")
    return hits


def _lint_banned_phrases(path: Path) -> list[str]:
    if path.name == "HISTORY.md":
        return []
    text = path.read_text(encoding="utf-8", errors="ignore")
    # Changelog satırlarında "(tarihsel" varsa o satırı atla
    warnings: list[str] = []
    rel = path.relative_to(ROOT)
    for i, line in enumerate(text.splitlines(), 1):
        if "tarihsel" in line.lower() or "append-only" in line.lower():
            continue
        if "*(tarihsel" in line:
            continue
        for phrase in _BANNED_PHRASES:
            if phrase in line:
                warnings.append(f"{rel}:{i}: yasaklı ifade «{phrase}»")
    return warnings


def _parse_master_b_statuses(master: str) -> dict[str, str]:
    """MASTER §12.1b satırları: B0…B7 → hücre metni."""
    found: dict[str, str] = {}
    for m in re.finditer(
        r"\|\s*\*\*B([0-7])\*\*\s*\|\s*([^|\n]+)\|", master
    ):
        found[f"B{m.group(1)}"] = m.group(2).strip()
    return found


def _status_is_kabul(cell: str) -> bool:
    """Kabul (ama 'Kabul değil' değil)."""
    return "Kabul" in cell and "Kabul değil" not in cell


def _lint_phase_consistency() -> list[str]:
    """MASTER §12.1b tek kaynak; BACKLOG/ADR-0017/ROADMAP ile çapraz kontrol."""
    out: list[str] = []
    master = MASTER.read_text(encoding="utf-8", errors="ignore") if MASTER.is_file() else ""
    adr = ADR_0017.read_text(encoding="utf-8", errors="ignore") if ADR_0017.is_file() else ""
    roadmap = ROADMAP.read_text(encoding="utf-8", errors="ignore") if ROADMAP.is_file() else ""
    readme = ADR_README.read_text(encoding="utf-8", errors="ignore") if ADR_README.is_file() else ""
    backlog_path = ROOT / "docs" / "BACKLOG.md"
    backlog = (
        backlog_path.read_text(encoding="utf-8", errors="ignore")
        if backlog_path.is_file()
        else ""
    )

    statuses = _parse_master_b_statuses(master)
    if not statuses:
        out.append("faz tutarsızlığı: MASTER §12.1b B0–B7 tablosu okunamadı")
        return out

    # Canlı dosyalarda bayat “henüz başlamadı / sırada B2” yasak (tarihsel satır hariç)
    stale_markers = (
        "B4 henüz başlatılmadı",
        "B4 sırada",
        "Sırada: B2",
        "Sırada:** B2",
        "B6 | Bekliyor",
        "B7 | Bekliyor",
        "**B6** | Bekliyor",
        "**B7** | Bekliyor",
    )
    for label, text in (
        ("MASTER.md", master),
        ("ROADMAP.md", roadmap),
        ("ADR-0017", adr),
        ("decisions/README.md", readme),
        ("BACKLOG.md", backlog),
    ):
        for i, line in enumerate(text.splitlines(), 1):
            if "tarihsel" in line.lower() or "*(tarihsel" in line:
                continue
            for marker in stale_markers:
                if marker in line:
                    out.append(
                        f"faz tutarsızlığı: {label}:{i} «{marker}» "
                        f"(MASTER §12.1b güncel)"
                    )

    # B5/B6 Kabul ise canlı metinde “B5/B6 … Kabul değil” kalmamalı (HISTORY hariç)
    for bn in ("B5", "B6"):
        cell = statuses.get(bn, "")
        if not _status_is_kabul(cell):
            continue
        bad_bits = (
            f"{bn} **Kabul değil**",
            f"{bn} uygulandı (inceleme",
            f"API-{bn} | **Uygulandı** — Kabul kararına hazır",
            f"API-{bn} | **Uygulandı** — inceleme",
        )
        for label, text in (
            ("MASTER.md", master),
            ("ROADMAP.md", roadmap),
            ("ADR-0017", adr),
            ("BACKLOG.md", backlog),
        ):
            for i, line in enumerate(text.splitlines(), 1):
                if "tarihsel" in line.lower():
                    continue
                for bit in bad_bits:
                    if bit in line:
                        out.append(
                            f"yanlış statü: {label}:{i} «{bit}» "
                            f"(MASTER {bn}=Kabul)"
                        )

    # BACKLOG kart Durum ↔ MASTER
    for bn, card in (
        ("B5", "API-B5"),
        ("B6", "API-B6"),
        ("B7", "API-B7"),
    ):
        cell = statuses.get(bn, "")
        # kart bloğu: ### [API-Bn] ... sonraki ### ye kadar
        m = re.search(
            rf"### \[{re.escape(card)}\](.*?)(?=\n### |\Z)",
            backlog,
            flags=re.S,
        )
        if not m:
            out.append(f"eksik referans: BACKLOG `{card}` kartı yok")
            continue
        block = m.group(1)
        dm = re.search(r"\*\*Durum:\*\*\s*(.+)", block)
        if not dm:
            out.append(f"eksik referans: BACKLOG {card} Durum satırı yok")
            continue
        durum = dm.group(1)
        if _status_is_kabul(cell) and "Kabul" not in durum:
            out.append(
                f"yanlış statü: BACKLOG {card} Durum≠Kabul "
                f"(MASTER {bn}={cell[:40]})"
            )
        if bn == "B7" and not _status_is_kabul(cell):
            # İnceleme / Kabul değil beklenir (Kabul öncesi)
            if "Kabul" in durum and "Kabul değil" not in durum and "UYGULANDI" not in durum:
                out.append(
                    f"yanlış statü: BACKLOG API-B7 «{durum[:48]}» "
                    f"↔ MASTER B7 «{cell[:48]}»"
                )
            if "Kabul değil" not in durum and "inceleme" not in durum.lower():
                out.append(
                    "yanlış statü: BACKLOG API-B7 inceleme/Kabul değil ifadesi yok "
                    f"(MASTER B7 henüz Kabul değil)"
                )

    # ADR-0017: B6’nın kendisi “Kabul değil” olmamalı (B7 Kabul değil aynı satırda OK)
    if _status_is_kabul(statuses.get("B6", "")):
        if "B6" in adr and "Kabul" not in adr:
            out.append("yanlış statü: ADR-0017 B6 Kabul ifadesi yok (MASTER B6 Kabul)")
        for i, line in enumerate(adr.splitlines(), 1):
            if "tarihsel" in line.lower():
                continue
            # "B6 … Kabul değil" ama B7 bağlamı değil
            if re.search(r"\bB6\b(?![^.\n]{0,40}\bB7\b).*Kabul değil", line):
                out.append(f"yanlış statü: ADR-0017:{i} B6 Kabul değil (MASTER Kabul)")

    return out


def _lint_adr_status_table() -> list[str]:
    """ADR dosyası **Durum:** ↔ decisions/README satırı (kaba)."""
    if not ADR_README.is_file():
        return []
    readme = ADR_README.read_text(encoding="utf-8", errors="ignore")
    warnings: list[str] = []
    decisions = ROOT / "docs" / "decisions"
    for adr in sorted(decisions.glob("ADR-*.md")):
        text = adr.read_text(encoding="utf-8", errors="ignore")
        m = re.search(r"\*\*Durum:\*\*\s*\*\*([^*]+)\*\*", text)
        if not m:
            continue
        status = m.group(1).split("(")[0].strip()
        # README satırında dosya adı + durum geçmeli
        if adr.name not in readme:
            warnings.append(f"decisions/README: {adr.name} indeks satırı yok")
            continue
        # Supersede / Taslak / Kabul / Kapandı
        row_hit = False
        for line in readme.splitlines():
            if adr.name.replace(".md", "") in line or adr.name in line:
                if status.split()[0] in line or (
                    "Supersede" in status and "Supersede" in line
                ):
                    row_hit = True
                    break
        if not row_hit:
            warnings.append(
                f"ADR durum drift: {adr.name} «{status}» ↔ decisions/README satırı"
            )
    return warnings


def lint_docs() -> list[str]:
    """Bayat metin / hash / faz tutarlılığı — uyarı listesi."""
    warnings: list[str] = []
    for path in _LIVE_MD:
        if not path.is_file():
            continue
        warnings.extend(_lint_hashes(path))
        warnings.extend(_lint_banned_phrases(path))
    warnings.extend(_lint_phase_consistency())
    warnings.extend(_lint_adr_status_table())
    return warnings


def _render_data_dictionary() -> str:
    """Django model meta → DATA_DICTIONARY.md (ayrı süreç: Django setup)."""
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
        help="Dosyayı yazma; AUTO drift veya kırık link varsa exit 1; lint UYARI",
    )
    parser.add_argument(
        "--lint-docs",
        action="store_true",
        help="Yalnız docs lint; ihlaller UYARI, exit 0",
    )
    parser.add_argument(
        "--lint-docs-strict",
        action="store_true",
        help="Docs lint ihlali exit 1 (CI soft→hard geçişi)",
    )
    args = parser.parse_args()

    if args.lint_docs or args.lint_docs_strict:
        warns = lint_docs()
        for w in warns:
            print(f"UYARI lint: {w}", file=sys.stderr)
        if not warns:
            print("docs_sync lint: OK")
        if args.lint_docs_strict and warns:
            return 1
        return 0

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
    lint_warns = lint_docs()

    if args.check:
        drift = original != updated or dict_original != dict_body
        if original != updated:
            print("docs_sync --check: MASTER.md AUTO blokları bayat", file=sys.stderr)
        if dict_original != dict_body:
            print("docs_sync --check: DATA_DICTIONARY.md bayat", file=sys.stderr)
        for err in link_errors:
            print(err, file=sys.stderr)
        for w in lint_warns:
            print(f"UYARI lint: {w}", file=sys.stderr)
        if drift or link_errors:
            return 1
        print("docs_sync --check: OK")
        if lint_warns:
            print(f"docs_sync --check: {len(lint_warns)} lint uyarısı (exit 0)")
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
    for w in lint_warns:
        print(f"UYARI lint: {w}", file=sys.stderr)
    return 1 if link_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
