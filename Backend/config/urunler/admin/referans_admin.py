from django.contrib import admin

from ..models import (
    Berraklik, KesimKalitesi, Koleksiyon, KopcaTipi, MihlamaTipi, OzelGun, Renk,
    RenkDerecesi, SertifikaKurumu, Stil, TasKesimi, TasMensei, TasTipi, Teknik,
    YasGrubu, ZincirTipi,
)

# --- basit seçim listeleri -------------------------------------------------
BASIT_LISTELER = [
    Koleksiyon, Renk, YasGrubu, Teknik, Stil, OzelGun, ZincirTipi, KopcaTipi,
    TasKesimi, MihlamaTipi, TasMensei, SertifikaKurumu, Berraklik, RenkDerecesi, KesimKalitesi,
]


class BasitListeAdmin(admin.ModelAdmin):
    list_display = ("ad", "kod", "sira", "aktif")
    list_editable = ("sira", "aktif")
    list_filter = ("aktif",)
    search_fields = ("ad", "kod")
    list_per_page = 50


for _model in BASIT_LISTELER:
    admin.site.register(_model, BasitListeAdmin)


# --- TasTipi: degerli alanı ayrıca gösterilmeli ----------------------------
@admin.register(TasTipi)
class TasTipiAdmin(admin.ModelAdmin):
    list_display = ("ad", "kod", "degerli", "sira", "aktif")
    list_editable = ("degerli", "sira", "aktif")
    list_filter = ("aktif", "degerli")
    search_fields = ("ad", "kod")
    list_per_page = 50


