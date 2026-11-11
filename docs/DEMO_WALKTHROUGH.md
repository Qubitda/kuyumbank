# Demo inceleme haritası

**Şifre (hepsi):** `DemoPortal1!`  
**Seed:** `python manage.py seed_demo_ops_samples` (commerce + örnek operasyonlar)

| Adım | Kim | Nerede bak | Örnek veri |
|------|-----|------------|------------|
| 1 Katalog | `demo_alici` | `/buyer/catalog` | Ürün `DEMO-YZK-001` · 3 varyant |
| 2 Quote/sipariş | `demo_alici` | Katalog detay → Sipariş | Kanal `KUYUMCU_PANEL` |
| 3 Sepet | `demo_alici` | `/buyer/cart` | Açık satır (varyant B) |
| 4 Sipariş | `demo_alici` | `/buyer/orders` | Sipariş #1 `OLUSTURULDU` |
| 4b Sevkiyat/iade | `demo_alici` | `/buyer/logistics` | `/shipments/` + `/returns/` (boş olabilir) |
| 5 RFQ | `demo_alici` | `/buyer/rfqs` | RFQ gönderilmiş + eşleştirme RFQ |
| 5b Finans | `demo_alici` | `/buyer/finance` | Cari + kredi (maskeli) |
| 6 Teklif (yayınlı) | `demo_tedarikci` | `/supplier/offers` | `DEMO-1..3` yayınlı |
| 6b RFQ havuzu | `demo_tedarikci` | `/supplier/rfqs` | Gönderilmiş RFQ; alıcı adı yok |
| 7 Teklif taslak | `demo_tedarikci` | `/supplier/offers` | `DEMO-DRAFT` |
| 8 Stok | `demo_tedarikci` | `/supplier/stock` | Depo `DEMOWH` + bakiye |
| 9 Sipariş ops | `demo_ops` | `/admin/orders` | Aynı sipariş (view_all) |
| 9b Finans ops | `demo_ops` | `/admin/finance` | Cari + ledger id (ad yok) |
| 10 RFQ eşleştirme | `demo_ops` | `/admin/rfq-match` | Öneri `ONERILDI` |
| 11 MFA UI | platform + `MFA_ENFORCE_PLATFORM` | `/login` | OTP adımı (demo’da kapalı olabilir) |
| 12 Act-as | `demo_ops` | `/admin/users` → user_id `2` (`demo_alici`) | Banner + «Act-as bitir» (AA-3) |
| 13 Ürün ops | `demo_ops` | `/admin/products` | Taslak→gönder; onay ayrı aktör (dört göz) |
| 14 QC / sevkiyat | `demo_ops` (okuma) | `/admin/qc` · `/admin/shipments` | Yazma `manage_qc` / `manage_shipment` |
| 15 Alıcı özet | `demo_alici` | `/buyer` | `/me/dashboard/` sayaçlar |
| 16 Profil | üç rol | `/buyer/profile` · `/supplier/profile` · `/admin/profile` | Ad/soyad; adres yazma `manage_users` |

Not: `demo_ops` seed sonrası `platform_admin` (eşleştirme yetkisi). `demo_tedarikci` → `tedarikci_sahip` (depo). Demo id: alici=`2`, tedarikci=`3`, ops=`4` (yerel seed).
