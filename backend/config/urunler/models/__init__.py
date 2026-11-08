"""Ürün modellerinin geriye dönük uyumlu dışa aktarım noktası.

Eski kullanım çalışmaya devam eder:
    from urunler.models import Urun, Kategori
"""
from .kategori import Kategori
from .referanslar import (
    Berraklik,
    Koleksiyon,
    KesimKalitesi,
    KopcaTipi,
    MihlamaTipi,
    OzelGun,
    Renk,
    RenkDerecesi,
    SertifikaKurumu,
    Stil,
    TasKesimi,
    TasMensei,
    TasTipi,
    Teknik,
    YasGrubu,
    ZincirTipi,
)
from .olcu import OlcuDegeri
from .urun import Urun
from .urun_kanal import UrunKanal
from .urun_tasi import UrunTasi
from .varyant import Varyant

__all__ = [
    "Berraklik",
    "Kategori",
    "KesimKalitesi",
    "Koleksiyon",
    "KopcaTipi",
    "MihlamaTipi",
    "OlcuDegeri",
    "OzelGun",
    "Renk",
    "RenkDerecesi",
    "SertifikaKurumu",
    "Stil",
    "TasKesimi",
    "TasMensei",
    "TasTipi",
    "Teknik",
    "Urun",
    "UrunKanal",
    "UrunTasi",
    "Varyant",
    "YasGrubu",
    "ZincirTipi",
]
