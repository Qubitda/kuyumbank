# ADR-0001 — Agent standartları ve faz sırası

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
