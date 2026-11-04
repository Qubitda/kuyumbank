# Kullanıcı ve rol modeli

## Kurallar

- Her kullanıcı tek bir `Firma` kaydına ve tek bir `rol` değerine bağlanır.
- Firma aynı anda alıcı ve tedarikçi olabilir; bu firma özelliği kullanıcı rolü değildir.
- Platform rolleri yalnızca `platform_mu=True` firmaya atanır.
- Alıcı rolleri yalnızca `alici_mi=True` firmaya atanır.
- Tedarikçi rolleri yalnızca `tedarikci_mi=True` firmaya atanır.
- `is_active`, `is_staff` ve `is_superuser`, iş rolünden ayrı Django hesap/yönetim alanlarıdır.
- `platform_super`, Django `is_superuser` anlamına gelmez.
- Rol grupları `rol:<rol_kodu>` adıyla otomatik oluşturulur. Admin ekranında Group ve doğrudan user permission ataması yapılmaz.

## Mevcut veriyi koruma

`Kullanici.firma` veritabanında geçici olarak `null=True` kalır. `blank=False` yeni admin/form kayıtlarında zorunluluk getirir; mevcut null kayıtları migration sırasında silmez veya varsayılan firmaya bağlamaz.

Önce şu salt okunur denetimi çalıştır:

```bash
python manage.py audit_user_assignments
```

Çıktıdaki eksik/uyumsuz kayıtlar gerçek firma bilgisine göre düzeltilmeden `firma` alanını veritabanında `null=False` yapmak güvenli değildir. Kullanıcı sayısı ve mevcut kayıtlar doğrulandıktan sonra ayrı bir veri migration'ı ve NOT NULL migration'ı hazırlanmalıdır.

## Rol ataması

Uygulama servislerinden rol/firma değişikliği için:

```python
from firmalar.role_services import assign_user_role

assign_user_role(user=user, firma=firma, rol="alici_satinalmaci")
```

Servis firma-rol uyumunu doğrular, kullanıcıyı kaydeder ve ilgili `rol:<rol_kodu>` grubunu eşitler. Doğrudan `user.groups` veya `user.user_permissions` ataması yapılmamalıdır.

## Yetki matrisi henüz tamamlanmadı

Bu aşamada rol grupları oluşturulup üyelikleri yönetilir; gruplara ürün, fiyat, sipariş, finans, mutabakat ve audit log izinleri verilmez. Kaynak mimari doküman rol × izin matrisinin tanımlanmasını istiyor ancak tüm 13 rol için ayrıntılı izinleri vermiyor. Bu nedenle varsayımsal izinler eklenmedi. Uygulama modülleri ve iş akışları netleşince izin matrisi ayrı olarak tanımlanmalıdır.
