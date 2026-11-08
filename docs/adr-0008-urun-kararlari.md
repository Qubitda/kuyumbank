# ADR-0008 — Ürün sahibi karar turu (Dilim 3.3 hazırlığı)

**Tarih:** 2026-11-08  
**Kaynak ADR:** [`docs/decisions/ADR-0008-faz3b-kur-fiyatlama-quote.md`](decisions/ADR-0008-faz3b-kur-fiyatlama-quote.md) (**Durum: Kabul edildi** — 2026-11-08)  
**Amaç:** §5 maddelerini karar verilebilir hale getirmek; ürün sahibi seçimleri aşağıda kayıtlıdır.  
**Kapsam dışı (korunur):** B-01 (hukuk görüşü bekleniyor — kod yok); B-06 (ertelendi — proforma, vergi yok).

**Dilim notu:** Dilim **3.3 = yalnız kur politikası**. Quote motoru, alıcı UI kırılımı ve teklif seçim kodu sonraki dilimlerdedir; yine de ADR Kabul için aşağıdaki ürün kararlarının netleşmesi gerekir.

---

## Kapsam dışı — dokunulmaz

### B-01 — Gizli platform hizmet payı
- ADR §2.8 / §6: hukuk görüşü gelmeden servis payı kalemi ve gizli yedirme **kodlanmaz**.
- Bu turda seçenek sunulmaz; mevcut sınır korunur.

### B-06 — Vergi / KDV
- ADR §2.9: ürün sahibi kararı (2026-11-08) — Faz 3 **proforma**; KDV hesaplanmaz/saklanmaz; mali müşavir şimdilik gerekmez.
- Bu turda yeniden açılmaz.

### Servis payı kaynağı / C sınıfı eşleşme
- ADR §5’te ayrı ÖNERİ satırları var; bu turda sorulmaz (B-01 ile bağlı / ADR-0007 kapısı sabit).

---

## 1. B-02 — Alıcı görünümü

### Mevcut ADR metni
> Varsayılan **yalnız toplam** (+ isteğe bağlı gram başı). Kırılım konfigle; **hukuk onayı olmadan kırılım açılmaz**. Servis payı **ayrı satır görünmez**. (§5 B-02; §2.8)

### Teknik bağlam
- Quote satırları (metal, işçilik, marj, taş…) iç hesap / snapshot içindir; alıcı API/yüzeyi ayrı görünürlük politikası taşır.
- Kör havuz: tedarikçi maliyeti ve kimliği alıcıya gitmez (ADR §7 test beklentisi).
- B-01 açık olduğu sürece “servis payı ayrı satır” zaten yasak; toplamın içinde gömülü tutmak da hukuk riskini kapatmaz — yalnızca görünürlük varsayılanını sabitler.

### Ürün sahibine soru
Alıcıya **varsayılan** olarak ne gösterilsin?

### Seçenekler

| # | Seçenek | Ticari sonuç | Teknik sonuç |
|---|---------|--------------|--------------|
| A | **Yalnız `toplam_vergisiz`** (+ isteğe bağlı gram başı birim) | Şeffaflık düşük; pazarlık/kırılım talebi azalır; hukuk onayı öncesi en güvenli yüzey | Alıcı serializer’da kalem listesi kapalı; kırılım feature-flag + hukuk kapısı |
| B | Toplam + seçilmiş “müşteri kalemleri” (ör. metal+işçilik; marj/servis gizli) | Kısmi şeffaflık; hangi kalemin müşteri kalemi olduğu sürekli ürün tartışması | Kalem tipi whitelist konfigi; yanlış whitelist = maliyet sızıntısı riski |
| C | Tam kırılım (tüm satırlar) | Azami şeffaflık; B-01/fatura uyumu ve kör havuz ihlali riski yüksek | Hemen hemen tüm Line’lar expose; hukuk onayı şart |

### Öneri
**A** — ADR §5 ile aynı; hukuk onayı gelmeden kırılım açılmaz.

### Karar yoksa etki
Alıcı yüzeyi / 3.6 kör havuz dilimi bloke; 3.3 kur politikası kodu başlayabilir ama ADR Kabul checklist’i (§10) tamamlanmaz.

---

## 2. B-03 — Quote TTL

### Mevcut ADR metni
> **Kanal bazlı** (B2B≠B2C). TTL ≤ ilgili kur gözleminin max gecikmesi. Sayı finans belirler. Değer yoksa quote yok. (§5 B-03; §2.4)

### Teknik bağlam
- `PriceQuote.gecerlilik_sonu` = üretim anı + TTL.
- Stale kur ile sessiz fiyat yok (K-019 / ADR §2.5–2.7); TTL, kur max gecikmesinden **uzun** olursa “geçerli quote + bayat kur” çelişkisi doğar.
- Sayısal saniye/dakika bu belgede sabitlenmez; politika şekli kararlaştırılır. Finans sonradan konfig değeri girer.

### Ürün sahibine soru
Quote geçerlilik süresi nasıl yönetilsin?

### Seçenekler

| # | Seçenek | Ticari sonuç | Teknik sonuç |
|---|---------|--------------|--------------|
| A | **Kanal bazlı TTL** (B2B ≠ B2C ayrı konfig); TTL ≤ o an kullanılan kur gözleminin max gecikmesi; değer yok → quote yok | Kanal riskine göre farklı kilit penceresi; finans kontrolü | `satis_kanali` → TTL map + kur max_age assert; eksik konfig fail-closed |
| B | Tek global TTL (tüm kanallar aynı) | Operasyon basit; B2C kısa / B2B uzun ihtiyacı karşılanmaz | Tek ayar; kanal alanı yok |
| C | Alıcı firmaya özel TTL override (+ kanal varsayılanı) | Büyük alıcılara özel pencere; sözleşme karmaşıklığı | Firma override tablosu; çözüm sırası + audit |

### Öneri
**A** — ADR §5; metal fiyatı hızlı değişir, kanal ayrımı şart; fail-closed.

### Karar yoksa etki
3.3’te kur max gecikme konfigi tasarlanabilir; quote üretimi (3.5) TTL olmadan fail-closed kalır — sayısal değer finansın, **politika şekli** ürünün.

---

## 3. B-04 — Kur sağlayıcı

### Mevcut ADR metni
> Aynı anda **tek aktif provider**; otomatik fallback yok. Manuel: neden + dört göz + audit. Max gecikme konfig. (§5 B-04)

### Teknik bağlam
- Mevcut `MetalKuru` / `DovizKuru` rapor §1385’e göre yeniden tasarlanacak (kaynak, gecikme, geçerlilik, kur tipi eksik) — **Dilim 3.3 çekirdeği**.
- Otomatik fallback: sessizce yanlış/eski kaynakla fiyat = finansal sapma + denetim kaybı.
- Manuel kur girişi: neden + dört göz + audit (ADR §2.5–2.7).

### Ürün sahibine soru
Aynı anda birden fazla kur sağlayıcı aktif olabilir mi? Sağlayıcı düşerse ne olsun?

### Seçenekler

| # | Seçenek | Ticari sonuç | Teknik sonuç |
|---|---------|--------------|--------------|
| A | **Tek aktif provider**; otomatik fallback yok; kesintide quote/kur yenileme durur; manuel giriş dört göz+audit | Kesintide satış durabilir; kaynak ve sorumluluk net | `aktif=True` tekil kısıt; health≠auto-switch; manuel path zorunlu audit alanları |
| B | Birincil + otomatik ikincil fallback | Kesintide süreklilik; hangi kurla satıldığı tartışmalı; arbitraj/uyumsuzluk | Failover state machine; snapshot’a “asıl vs kullanılan” provider yazımı |
| C | Çoklu provider ortalama / blend | “Piyasa ortası” iddiası; lisans ve metodoloji yükü | Ağır hesap; B-04 basit modelini bozar |

### Öneri
**A** — tek doğruluk kaynağı; stale/yanlış kaynakla sessiz fiyat yok ilkesiyle uyumlu.

### Karar yoksa etki
**Dilim 3.3 model/servis tasarımı bloke** (aktif provider kısıtı, max gecikme, manuel path).

---

## 4. B-05 — Kur tipi

### Mevcut ADR metni
> Alıcı ve tedarikçi tarafı için **ayrı tipler** (ör. satış/alış); ikisi de snapshot’a. Seçim finansın. (§5 B-05; PriceQuote kur gözlemleri)

### Teknik bağlam
- Alıcı satış fiyatı ile tedarikçi maliyet kıyası farklı spread kullanabilir.
- Snapshot’a her iki gözlem yazılmazsa sonradan “hangi kurla hesaplandı?” denetimi yapılamaz.
- Hangi enum değerlerinin (alış/satış/efektif/…) finans tarafından seçileceği konfigdir; ürün kararı **ayrı mı / tek mi** ayrımıdır.

### Ürün sahibine soru
Alıcı fiyatı ve tedarikçi maliyet tarafı aynı kur tipini mi, ayrı tipleri mi kullansın?

### Seçenekler

| # | Seçenek | Ticari sonuç | Teknik sonuç |
|---|---------|--------------|--------------|
| A | **Ayrı kur tipleri** (ör. alıcı=satış, tedarikçi=alış); ikisi de quote snapshot’ta | Spread bilinçli; marj görünürlüğü iç raporlarda netleşir | İki konfig anahtarı + iki gözlem FK/JSON; eksik tip → quote yok |
| B | Tek ortak kur tipi (her iki taraf aynı gözlem) | Basit; alış-satış spread’i modele girmez (marj başka yerde) | Tek gözlem; maliyet/satış ayrımı kur katmanında yok |
| C | Yalnız alıcı kur tipi zorunlu; tedarikçi tipi opsiyonel (yoksa alıcı tipi) | İlk dilimde hızlı; maliyet denetimi zayıf | Koşullu ikinci gözlem; “opsiyonel” sonradan zorunlu yapılınca migration/analitik kırılır |

### Öneri
**A** — ADR §5; denetlenebilir spread; finans hangi kodları seçeceğini konfigde belirler.

### Karar yoksa etki
**Dilim 3.3 kur gözlem şeması** (alanlar/kısıtlar) netleşmez; 3.5 snapshot sözleşmesi ertelenir.

---

## 5. Çoklu YAYINDA teklif — seçim sırası

### Mevcut ADR metni
> Alıcı seçmez (kör havuz). Sıra: `oncelik` ↓, sonra en düşük maliyet, sonra deterministik eşitlik bozucu (ör. `teklif.id`). Seçilen teklif quote’a yazılır. (§5; §2.4 giriş)

### Teknik bağlam
- `teklif_id` verilmezse platform seçer; alıcı kimlik görmez.
- `oncelik` alanı vardır; ADR-0009 H2 ile **yalnız platform** yazar (tedarikçi POST ile aşamaz).
- “En düşük maliyet” tanımı model bazlıdır (METAL_BAZLI vs GRAM_BIRIM vs SABIT_PARCA) — seçim anında iç maliyet skoru gerekir; alıcıya gösterilmez.
- Eşitlikte non-deterministik seçim = aynı girdide farklı quote → finansal/repro riski.

### Ürün sahibine soru
Aynı varyantta birden fazla YAYINDA+geçerli+eşleşme onaylı teklif varken platform hangi sırayla seçsin?

### Seçenekler

| # | Seçenek | Ticari sonuç | Teknik sonuç |
|---|---------|--------------|--------------|
| A | **`oncelik` ↓ → en düşük iç maliyet → `teklif.id` ↑** | Platform ticari tercihi (`oncelik`) önce; sonra maliyet optimizasyonu; kör havuz korunur | Sıralı queryset/servis; maliyet skoru saf fonksiyon; her zaman deterministik |
| B | Yalnız en düşük iç maliyet → `id` (oncelik yok sayılır) | Operasyonel `oncelik` anlamsızlaşır; platform müdahalesi zayıf | Basit sort; H2 `oncelik` alanı ölü kalır |
| C | Rastgele / rotasyon (eşit yük dağıtımı) | Tedarikçiler arası “adil dağıtım” iddiası; fiyat ve audit öngörülemez | Seed/rotasyon state; aynı sepette farklı teklif riski |

### Öneri
**A** — ADR §5; mevcut `oncelik` + deterministik eşitlik bozucu.

### Karar yoksa etki
3.3’ü bloklamaz; `PricingService.quote` teklif seçimi (3.5+) ve eşleşme testleri netleşmez. ADR Kabul için yine de cevap gerekir.

---

## Karar kayıt alanı (ürün sahibi)

| ID | Seçilen | Tarih | Not |
|----|---------|-------|-----|
| B-02 | **A** | 2026-11-08 | Yalnız toplam |
| B-03 | **A** | 2026-11-08 | Kanal bazlı TTL |
| B-04 | **A** | 2026-11-08 | Tek aktif provider; fallback yok |
| B-05 | **A** | 2026-11-08 | Ayrı alıcı/tedarikçi kur tipi |
| Çoklu YAYINDA | **A** | 2026-11-08 | `oncelik`↓ → maliyet↑ → `id`↑ |

ADR-0008 **Kabul edildi** (ürün sahibi). Agent kendi taslağını onaylamaz.

**Sonraki geliştirme:** Dilim **3.3 kur politikası** — quote motoruna geçilmez.
