# ADR-0006 — Faz 2.1 düzeltme kararları

**Durum:** Kabul edildi  
**Tarih:** 2026-11-08  
**Bağlı:** ADR-0005 (Kabul); `faz2-1-dogrulama-raporu.md`  
**Onay:** Ürün sahibi — 2026-11-08

---

## 1. Bağlam

Faz 2.1 ADIM 1 doğrulaması B1–B4 / O1–O6 açıklarını listeledi. Bu ADR, ADIM 2 uygulama sınırlarını bağlar.

---

## 2. Kararlar

| Kod | Karar |
|-----|--------|
| **B1** | Tedarikçi teklif admin: `durum`, `onaylayan`, `onay_zamani`, `eslestirme_*`, `hedef_urun`, `esdegerlik_seviyesi` salt okunur. `tedarikci` sunucuda `request.user.firma` atanır. Varyant FK tek selector ile kapsamlı. Durum geçişleri yalnız servis. |
| **B2** | `assign_user_role(actor=..., user=..., firma=..., rol=...)`; `require_perm` + tenant; audit actor=değiştiren; hedef kullanıcı detail’de. Firma değişikliği yalnız platform (`manage_all_users` / view-all). KullaniciAdmin Firma/rol seçenekleri tenant kapsamlı. |
| **B3** | `teklif_eslestir_oner`: hedef görünür/uygun değilse genel hata (kimlik ipucu yok). Güven hesabı tedarikçi kanıtından oracle üretmez (`tedarikci_kodu` ↔ ürün kimliği). ONAYLANDI/AYRILDI iken öneri reddedilir (lock sonrası). `eslestirme_kaniti` izinli anahtar + string + uzunluk. Fail audit atomic dışı. |
| **B4a** | Gram bandı hesabı (`VARYANT_GRAM_BANDI_ORAN` / override alanları); bant dışı öneri nedenli red + audit; `eslestirmeyi_onayla` hedef ayar/bant yeniden doğrular. |
| **B4b** | `urunleri_birlestir` **ertelendi** (bu fazda eklenmez). Kapsam/varyant taşıma sonraki ADR. |
| **O1** | `onay_bekliyor`: tedarikçi Urun/Varyant/inline salt okunur. `geri_cek` → taslak (sahiplik+perm+audit). Onaylıda kritik alan değişimi engellenir; `taslaga_al` + yeniden onay. |
| **O2** | Unique `urun_kimlik_ab_anahtar_uniq` → A/B + dolu anahtar + `onay_durumu != 'reddedildi'`. Migration `0007`. `onaya_gonder` aktif çakışmayı serviste genel hata + fail audit ile önler; `IntegrityError` yarışı genel hataya maplenir. |
| **O3** | Fail audit kalıcılığı — aşağıda. |
| **O4** | Toplu Reddet: `_selected_action` çoklu ID listesi doğru parse edilir. |
| **O5** | `onayla` / `yayina_al`: aktör ≠ son başarılı `urun.onaya_gonder` aktörü (yoksa `olusturan_kullanici`); ihlalde fail audit. |
| **O6** | `approve_teklif` / `manage_sozlesme` servis bağlama **Faz 3’e ertelendi**. |

### O1 kritik alanlar (onaylı kilit)

`kimlik_sinifi`, `kimlik_anahtari`, `ayar_id`, `kategori_id`, `fiyat_tipi`, `ad` — değişim engeli; düzenleme için `taslaga_al`.

### O2 migration

| Madde | İçerik |
|-------|--------|
| Dosya | `urunler/migrations/0007_o2_kimlik_uniq_reddedildi_haric.py` |
| Hedef | Partial unique: `kimlik_sinifi ∈ {A,B}` ∧ `kimlik_anahtari != ''` ∧ `onay_durumu != 'reddedildi'` |
| İleri | Kısıt gevşer; mevcut veriyi bozmaz / satır silmez |
| Reverse | Eski kısıta dönüş öncesi çakışma kontrolü; varsa `RuntimeError` (genel mesaj, satır silinmez) |

### O3 — `record_audit_durable` (üretim davranışı)

**Üretim (autocommit veya dış `transaction.atomic`):**

1. `domain_atomic()` **içinde** çağrı → `RuntimeError` (fail audit domain rollback ile silinmesin diye yasak).
2. Herhangi bir `transaction.atomic` bloğu içindeyse → audit satırı **ayrı DB bağlantısı (sidecar)** ile yazılır ve o bağlantıda `commit` edilir. Dış atomic sonra rollback olsa bile fail audit **kalır**.
3. Atomic dışında (autocommit) → normal `record_audit` yazımı; hemen kalıcıdır.

**Test sapması (yalnız TestCase):** Sidecar, henüz commit edilmemiş `actor_id` görürse FK `IntegrityError` alabilir. Bu durumda aynı test bağlantısına fallback yapılır (assert görünür; test sonunda rollback olur). Production’da kullanıcı zaten commit’lidir → sidecar yolu kullanılır. Kalıcılık `TransactionTestCase` ile kanıtlanır.

### Gram bandı (B4a)

- `gram_bandi_min/max` doluysa onlar; değilse `varyant.gram * (1 ± VARYANT_GRAM_BANDI_ORAN)`.
- Teklif `gram` band dışındaysa öneri/onay reddedilir (nedenli mesaj + audit).

### Bilinçli sınır — teklif `durum` (Faz 3)

Admin’de `TedarikciTeklif.durum` (ve onay/eşleştirme alanları) **salt okunur**; formdan durum geçişi yok. Durum makinesi / `approve_teklif` servisleri **Faz 3’e ertelendi**. Bu bilinçli sınırdır; admin üzerinden teklif yayınlama yapılmaz.

---

## 3. Non-goals

- Faz 3 fiyat motoru / `approve_teklif` / teklif durum servisi
- `urunleri_birlestir` implementasyonu
- Üretim migrate (ayrı onay)

---

## 4. Onay checklist

- [x] B1–B5 / O1–O5 uygulama kabul  
- [x] B4b birleştir ertelendi kabul  
- [x] O2 migration planı + dosya  
- [x] O3 sidecar durable kabul  
- [x] O6 Faz 3 erteleme kabul  
- [x] Durum: **Kabul edildi**
