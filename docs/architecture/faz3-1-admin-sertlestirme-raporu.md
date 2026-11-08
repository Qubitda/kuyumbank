# ADR-0009 — Admin yüzey sertleştirme uygulama raporu

**Tarih:** 2026-11-08  
**ADR:** 0009 (**Kabul**)  
**Durum:** Uygulandı (H1–H5 + D1)

## Değiştirilen dosyalar

| Dosya | Sorumluluk |
|-------|------------|
| `firmalar/admin/kullanici_admin.py` | H1: privilege alanları yalnız `manage_all_users`; POST escalate engeli |
| `fiyatlama/selectors/tenant.py` | H3: `user_may_see_teklif_maliyet` |
| `fiyatlama/admin/admin.py` | H2 kilit + H3 maliyet görünürlüğü + save_model koruması |
| `fiyatlama/services/teklif_servisi.py` | H5(a): yeni versiyonda eşleştirme sıfır |
| `urunler/admin/urun_admin.py` | H4: O1 kilidi Varyant/UrunTasi/UrunKanal + list_editable |
| `requirements.txt` | D1: UTF-8 + `Pillow==12.0.0` |
| `firmalar/tests/test_admin_h1_privileges.py` | H1 testleri |
| `fiyatlama/tests/test_admin_h2_h3_h5.py` | H2/H3/H5 testleri |
| `urunler/tests/test_admin_h4_o1_surface.py` | H4 testleri |
| `docs/decisions/ADR-0009-…` | Kabul |
| `docs/architecture/faz3-1-sonrasi-guvenlik-denetimi.md` | Denetim kaydı |

## Testler (DOĞRULANDI)

```text
python manage.py check → 0 issue
python manage.py makemigrations --check --dry-run → No changes detected
python manage.py test firmalar.tests urunler.tests fiyatlama.tests tanimlar.tests
→ Ran 176 tests — OK (H3 sonrası s7 testi güncellendi)
```

## Riskler / açık

- Orta öncelikli denetim maddeleri (slug, audit admin, `approve_firma`, `cozumle` sıra) bu ADR dışı.
- Sonraki: dilim 3.2 veya ADR-0008.
