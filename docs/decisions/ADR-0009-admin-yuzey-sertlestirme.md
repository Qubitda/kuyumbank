# ADR-0009 — Admin yüzey sertleştirme (post-3.1)

**Durum:** Kabul edildi  
**Tarih:** 2026-11-08  
**Bağlı:** ADR-0003, ADR-0005, ADR-0006, ADR-0007 (Kabul); denetim: [`faz3-1-sonrasi-guvenlik-denetimi.md`](../architecture/faz3-1-sonrasi-guvenlik-denetimi.md)  
**Onay:** Ürün sahibi — 2026-11-08

**Kapsam notu:** Bu ADR, dilim 3.2 (K-007/K-008) ve ADR-0008’den **önce** kapanması gereken admin/servis deliklerini bağlar. Kabul olmadan kod yok.

---

## 1. Bağlam

Dilim 3.1 teklif yaşam döngüsünü serviste kurdu. Bağımsız denetim: servis sağlam; admin ve maliyet görünürlüğü kuralları atlıyor veya yanlış kapatıyor (bulgu H1–H5). Faz 2.1 O1 yalnız kısmi yüzeyde.

---

## 2. Kararlar (öneri — Kabul sonrası bağlayıcı)

| Kod | Karar |
|-----|--------|
| **H1** | `is_staff` / `is_superuser` / `user_permissions` / `groups`: yalnız platform + `manage_all_users` (veya eşdeğer) düzenler. Tenant admin formunda bu alanlar yok veya readonly. Test: `tedarikci_sahip` / `alici_yonetici` bayrak yazamaz. |
| **H2** | `TedarikciTeklif` **YAYINDA** (ve tercihen `ONAY_BEKLIYOR`): fiyat/gram/model/geçerlilik/`oncelik`/`stok_adet` admin’de readonly veya `has_change_permission` false (platform istisnası yoksa). Değişiklik yalnız `yeni_versiyon_olustur` + onay. `oncelik` tedarikçi tarafından set edilmez (ADR-0008 seçim sırası platform alanı). |
| **H3** | Maliyet görünürlüğü ayrılır: **alıcı** → maliyet yok; **tedarikçi** → yalnız **kendi** teklifinin `birim_fiyat` / `iscilik_override` (ve gerekirse gram); **platform** → tümü. `user_may_see_fiyat_maliyet` bölünür veya `user_may_see_own_teklif_maliyet` eklenir. Alıcıya sızıntı yok. |
| **H4** | ADR-0006 **O1** kilidi tüm ürün yüzeylerine: `VaryantAdmin`, `UrunTasiAdmin`, `UrunKanalAdmin` (+ ilgili inline’lar). `onay_bekliyor` iken tedarikçi `list_editable` dahil yazamaz. Test: bağımsız admin + changelist. |
| **H5** | `yeni_versiyon_olustur`: (a) `eslestirme_durumu` / `hedef_urun` / kanıt **boşaltılır** (otomatik onay yok) **veya** (b) gram bandı + hedef tutarlılık `eslestirmeyi_onayla` ile aynı kontrollerden geçer; aksi halde ONAY_BEKLIYOR + eşleşme bekliyor. Tercih: **(a)** daha küçük ve geri dönüşü kolay — VARSAYIM aksi ürün sahibi (b) demedikçe. |
| **D1** | `requirements.txt` UTF-8 (BOM’suz); `Pillow` pin (ImageField kullanılıyor). Encoding düzeltmesi D1 ile birlikte. |

### Bilinçli ertelenen (bu ADR dışı)

- K-007/K-008, `cozumle` sıra → dilim 3.2  
- Quote / kur / geçerlilik cron → ADR-0008  
- AuditOlay admin + immutability, `approve_firma` servisi, slug stratejisi → sonraki sertleştirme  
- `islcilik_dahil_mi` rename → pahalı; dokunulmaz  

---

## 3. Migration

H1–H5 için şema gerekmez (beklenen). D1 yalnız requirements. H5 (a) veri migration istemez.

---

## 4. Testler (zorunlu, çalıştırılacak)

- H1: tenant rolü superuser/staff yazamaz; platform yazabilir.  
- H2: YAYINDA alan admin save reddi veya readonly; versiyon yolu çalışır.  
- H3: tedarikçi kendi teklifinde birim_fiyat görür/yazar; alıcı görmez; başka tedarikçi yok.  
- H4: `onay_bekliyor` iken VaryantAdmin / list_editable red.  
- H5: yeni versiyonda eşleşme boş (veya bant ihlali red); predicate false.  
- Mevcut suite regresyon (164+).

---

## 5. Non-goals

DRF, stok, finans, ADR-0008 quote motoru, K-007/K-008 şema.

---

## 6. Onay checklist

- [x] H1–H5 + D1 metni ürün sahibi tarafından kabul  
- [x] Durum: **Kabul edildi** (yalnız ürün sahibi)  
- [x] Uygulama + test + [`faz3-1-admin-sertlestirme-raporu`](../architecture/faz3-1-admin-sertlestirme-raporu.md)  

---

## 7. Uygulama sırası (Kabul sonrası)

Tek PR/dilim: H1 → H4 → H3 → H2 → H5 → D1; sonra tam test suite; rapor.
