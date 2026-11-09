from django.contrib import admin

from belgeler.models import Document, TasSertifikaBelgesi
from belgeler.selectors.tenant import scope_document_queryset


class _ImmutableAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Document)
class DocumentAdmin(_ImmutableAdmin):
    list_display = ("id", "firma", "tip", "baslik", "storage_key", "olusturma_tarihi")
    list_filter = ("tip",)
    list_select_related = ("firma",)
    readonly_fields = [f.name for f in Document._meta.fields]

    def get_queryset(self, request):
        return scope_document_queryset(
            super().get_queryset(request), request.user
        )


@admin.register(TasSertifikaBelgesi)
class TasSertifikaBelgesiAdmin(_ImmutableAdmin):
    list_display = ("id", "document", "urun_tasi", "teklif_tas", "olusturma_tarihi")
    list_select_related = ("document", "urun_tasi", "teklif_tas")
    readonly_fields = [f.name for f in TasSertifikaBelgesi._meta.fields]

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related("document")
        doc_ids = scope_document_queryset(
            Document.objects.all(), request.user
        ).values_list("pk", flat=True)
        return qs.filter(document_id__in=doc_ids)
