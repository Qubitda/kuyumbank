# ADR-0001 — Agent standartları ve faz sırası

> **Arşiv notu:** Bu ADR metni 2026-11-09 tarihinde `KUYUMBANK_MASTER.md` §6.3 arşivinden taşındı; içerik değiştirilmedi. Artık var olmayan dosyalara giden bağlantılar düz metne çevrildi. Güncel karar durumu: [README](README.md).

**Durum:** Kabul edildi  
**Tarih:** 2026-11-08  
**Bağlam:** Faz 0

## Karar

1. Proje bağlayıcı agent talimatı kök `AGENTS.md` dosyasıdır.
2. Cursor platformu kullanıldığı için skill yolu `.cursor/skills/<ad>/SKILL.md` olur (`.agent/skills` değil).
3. İnce her zaman-uygula kuralı: `.cursor/rules/kuyumbank-core.mdc`.
4. Geliştirme faz sırası kullanıcının verdiği 0–8 sırasıdır; rapor §14 ile uyumlu öz: önce kimlik/tenant, sonra katalog/teklif/fiyat, sonra stok/sipariş, finans, operasyon, API, prod.
5. İş kuralı kaynağı: `docs/Kuyumbank_Is_Analizi_Teknik_Analiz_Raporu.md` (K-* ve §9).
6. Django resmi docs/kaynak kodu framework referansıdır; proje skill’i değildir. Skill’ler Kuyumbank kurallarını taşır.
7. Denetimde Ek kural A (kanıt etiketleri) ve Faz 0’da Ek kural B (değişiklik sınırı) bağlayıcıdır.

## Sonuçlar

- Agent görev başında tüm dokümanı yeniden okumaz; ilgili skill + ADR yeterlidir.
- Faz atlanmaz; özellikle Faz 1 tamamlanmadan sipariş/finans yazılmaz.
- Kanıtsız bulgu ve çalıştırılmamış “yeşil test” iddiası geçersizdir.

---

## Doküman düzeni — **Kabul** (U-016; ürün sahibi Emre, 2026-11-09)

> Eski "docs/ altında yalnız tek dosya" kuralı yerine **"her bilgi tek yerde"** bağlayıcıdır.

**Gerekçe:** Tek dosya; farklı yaşam döngülerine sahip içeriği (canlı durum, değişmez ADR'ler, iş havuzu,
tarihçe) birlikte tutuyordu → tekrarlanan durum satırları çelişti (drift) ve her okuma ~74K token tuttu.

**Karar:** "Tek dosya" yerine **"her bilgi tek yerde"**:

| Dosya | İçerik | Değişme |
|-------|--------|---------|
| `docs/MASTER.md` | Vizyon, standartlar, tek durum matrisi, sıradaki iş (≤ ~300 satır) | Her dilimde |
| `docs/decisions/` | ADR dosyaları + indeks | Kabul sonrası değişmez (yerine geçen ADR) |
| `docs/BACKLOG.md` | İş/karar kartları | Sürekli |
| `docs/ROADMAP.md` | Hedef mimari, capability gap, faz yol haritası | Planlama |
| `docs/HISTORY.md` | Faz tarihçesi | Yalnız eklenir |
| `docs/RUNBOOK.md` | Kurulum / işletim / prod öncesi kontrol | Altyapı değişince |
| `docs/DATA_DICTIONARY.md` | **Otomatik** (modellerden) | Elle düzenlenmez |

Kural: `python scripts/docs_sync.py` AUTO blokları ve veri sözlüğünü koddan üretir; CI `--check` ile bayat
doküman ve kırık bağlantıyı reddeder. Agent: MASTER + yalnız ilgili ADR okur. Yeni faz raporu / ikinci yol haritası /
ayrı rapor dosyası yine **açılmaz**.
