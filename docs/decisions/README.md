# Mimari kararlar (ADR)

Onaylanmış kararlar burada tutulur. Agent varsayım yaptığında geri dönüşü kolay çözüm + yeni ADR yazar.

| ADR | Konu | Durum |
|-----|------|--------|
| [ADR-0001](ADR-0001-agent-standartlari.md) | Agent standartları, skill yolu, faz sırası | Kabul |
| [ADR-0002](ADR-0002-runtime-ve-bagimliliklar.md) | Django/Python pin, PostgreSQL, doğrudan requirements | Kabul |
| [ADR-0003](ADR-0003-faz1-kimlik-rbac.md) | Faz 1: 8 platform rolü, firma NOT NULL, K-004, dağıtık permissions, izolasyon testleri | Kabul |
| [ADR-0004](ADR-0004-modular-python-organizasyon.md) | Modüler Python paket/dosya organizasyonu (`models/`, `services/`, `selectors/`, …) | Kabul |
| [ADR-0003 addendum](ADR-0003-addendum-view-all-scope.md) | `view_all_tenants` quality/logistics/support’tan çıkarıldı | Kabul |
| [ADR-0005](ADR-0005-katalog-platform-ownership.md) | Katalog platform ownership (Faz 2) | Kabul |
| [ADR-0006](ADR-0006-faz2-1-kararlar.md) | Faz 2.1 düzeltme kararları (B1–O6) | Kabul |
| [ADR-0007](ADR-0007-faz3-fiyatlama.md) | Faz 3a: teklif yaşam döngüsü (3.1 uygulandı), K-007/K-008 (3.2 açık) | Kabul |
| [ADR-0008](ADR-0008-faz3b-kur-fiyatlama-quote.md) | Faz 3b: kur, fiyat hesabı, PriceQuote, görünürlük | **Taslak** |

Uygulama tasarımı: [`docs/architecture/faz1-kimlik-gecis-tasarimi.md`](../architecture/faz1-kimlik-gecis-tasarimi.md)  
Doğrulama: [`docs/architecture/faz1-dogrulama-raporu.md`](../architecture/faz1-dogrulama-raporu.md)  
Faz 2 etki: [`docs/architecture/faz2-etki-analizi.md`](../architecture/faz2-etki-analizi.md)  
Faz 2.1: [`docs/architecture/faz2-1-dogrulama-raporu.md`](../architecture/faz2-1-dogrulama-raporu.md)  
Faz 3 etki: [`docs/architecture/faz3-etki-analizi.md`](../architecture/faz3-etki-analizi.md)  
Faz 3.1 uygulama: [`docs/architecture/faz3-1-uygulama-raporu.md`](../architecture/faz3-1-uygulama-raporu.md)  
Mevcut mimari: [`docs/architecture/mevcut-mimari.md`](../architecture/mevcut-mimari.md)
