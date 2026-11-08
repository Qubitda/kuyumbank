# Faz 3a / Dilim 3.1 — Teklif yaşam döngüsü uygulama raporu

**Tarih:** 2026-11-08  
**ADR:** 0007 (Kabul) §2.1 + §3 migration adım 1 + §7 teklif testleri + §8 dilim 3.1  
**Durum:** Kod tamam; COMMIT yok (talimat)

## Değiştirilen / oluşturulan dosyalar (sorumluluk)

| Dosya | Sorumluluk |
|-------|------------|
| `fiyatlama/models/tedarikci_teklif.py` | `versiyon`, `onceki_teklif`, geçerlilik tarihleri; varyant `PROTECT`; YAYINDA partial unique (kodlu/kodsuz); geçerlilik check; `clean()` YAYINDA tarih zorunluluğu |
| `fiyatlama/migrations/0005_faz3_1_teklif_yasam_dongusu.py` | Alanlar + CASCADE→PROTECT + eski `teklif_tedarikci_kod_uniq` kaldırma + aktif çakışma unique + tarih check; reverse destekli |
| `fiyatlama/services/teklif_servisi.py` | Durum makinesi (`onaya_gonder` / `yayina_al` / `pasifle` / `yeniden_yayinla` / `yeni_versiyon_olustur`); sahiplik; `require_perm`; dört göz; versiyon swap sırası; audit (başarı atomic içi, fail durable) |
| `fiyatlama/selectors/tenant.py` | `teklif_eslestirme_uygun_mu` predicate (quote yok) |
| `fiyatlama/admin/admin.py` | `durum`/servis alanları readonly; admin action → servis |
| `fiyatlama/tests/test_teklif_yasam_dongusu.py` | Geçiş, sahiplik, yetki, dört göz, çakışma, PROTECT, geçerlilik, predicate, tenant, audit |
| `fiyatlama/tests/test_teklif_swap_atomic.py` | Swap rollback + fail audit durable (`TransactionTestCase`) |
| `fiyatlama/tests/test_migration_0005.py` | İleri/reverse migration |
| `docs/architecture/mevcut-mimari.md` | Teklif servisi satırı güncellendi |
| `docs/architecture/faz3-1-uygulama-raporu.md` | Bu rapor |

## VARSAYIM listesi (ADR’de adlandırılmamış)

| Varsayım | Seçim | Gerekçe |
|----------|--------|---------|
| Versiyon alanı | `versiyon` (`PositiveIntegerField`, default 1) | ADR-0007 Netleştirme §3 — en küçük tamsayı sürüm |
| Önceki bağ | `onceki_teklif` (`FK self`, `SET_NULL`, `related_name=sonraki_versiyonlar`) | Swap’te kilitlenecek önceki satır |
| Dört göz gönderen | Son başarılı `AuditOlay` `teklif.onaya_gonder` aktörü | Ürün onayı ile aynı desen; ayrı `gonderen` kolonu yok |
| Yeni versiyon + dört göz | `yeni_versiyon_olustur` ayrıca `teklif.onaya_gonder` success audit yazar | Onayda gönderen = versiyonu açan tedarikçi personeli |
| Global kod unique | `teklif_tedarikci_kod_uniq` kaldırıldı; aktif çakışma yalnız `YAYINDA` partial unique | Aynı `tedarikci_kodu` ile versiyon satırı zorunlu; ADR aktif çakışma yalnız YAYINDA |
| Yeni versiyon eşleştirme | Eski satırın `eslestirme_*` / `hedef_urun` kopyalanır; boşaltılmaz | Kimlik aynı varyant; migration backfill hâlâ yok (`eslestirme_durumu=''` legacy) |
| `pasifle` aktör | Platform (`approve_teklif`) veya sahip tedarikçi (`manage_own_teklif`) | Operasyonel kapatma |

## Testler (DOĞRULANDI)

```text
python manage.py check
→ System check identified no issues (0 silenced)

python manage.py makemigrations --check --dry-run
→ No changes detected

python manage.py test firmalar.tests urunler.tests fiyatlama.tests tanimlar.tests
→ Ran 164 tests in ~166s — OK
  (önceki 143 + dilim 3.1 yeni testler)
```

Kanıt sınıfları: `test_teklif_yasam_dongusu`, `test_teklif_swap_atomic`, `test_migration_0005`.

## Bulgular

- **DOĞRULANDI:** Durum geçişleri yalnız `teklif_servisi` — admin `durum` readonly (`admin.py` `_servis_alanlari`).
- **DOĞRULANDI:** Versiyon swap sırası eski PASIF → yeni YAYINDA; ortada hata → eski YAYINDA (`test_swap_rollback_keeps_eski_yayinda`).
- **DOĞRULANDI:** `varyant` `on_delete=PROTECT` (`tedarikci_teklif.py` L40–44; `test_protect_varyant`).
- **DOĞRULANDI:** Eşleşme predicate quote çağırmaz (`selectors/tenant.py` `teklif_eslestirme_uygun_mu`).
- **DOĞRULANDI:** `is_superuser` kısa yolu yok (`test_superuser_no_shortcut`).
- **PLANLAMA BULGUSU:** Dilim 3.2 (K-007/K-008, PricingService, ADR-0008) kapsam dışı; `hesapla()` değişmedi.

## Açık kalanlar

- Sözleşme yaşam döngüsü / immutability (ADR-0007 diğer dilimler).
- Quote motoru + çoklu YAYINDA seçim sırası (ADR-0008).
- Üretim DB migrate bu oturumda çalıştırılmadı (yalnız yerel).

## Riskler

- Yerel DB’de 0005 ilk uygulanışında `RemoveConstraint` dosyaya sonradan eklendi; geliştirme DB’de `teklif_tedarikci_kod_uniq` index’i elle düşürüldü. Taze migrate (0004→0005) veya test DB sorunsuz. Mevcut geliştirme DB’de `showmigrations` 0005 uygulı görünüyorsa index yokluğunu doğrulayın.
- `yeni_versiyon` eşleştirmeyi kopyalar; platform yeniden onay istemez (VARSAYIM). Kapı hâlâ `onaylandi` + `hedef_urun` tutarlılığı ister.
