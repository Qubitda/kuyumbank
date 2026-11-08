"""
Geriye dönük uyumluluk shimi.
Hesaplama mantığı `fiyatlama.services.fiyat_hesaplama`'ya taşındı.
Yeni kodda doğrudan oradan import edin.
"""
from fiyatlama.services.fiyat_hesaplama import hesapla, ISTENED_HASSASIYET, _d  # noqa: F401
