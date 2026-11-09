from django.contrib import admin

from siparis.models import Cart, CartLine, CheckoutAttempt, Order, OrderLine
from siparis.selectors.tenant import scope_cart_queryset


class _SiparisReadOnlyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class CartLineInline(admin.TabularInline):
    model = CartLine
    extra = 0
    can_delete = False
    fields = ("varyant", "price_quote", "miktar", "birim", "guncelleme_tarihi")
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Cart)
class CartAdmin(_SiparisReadOnlyAdmin):
    list_display = ("id", "alici_firma", "olusturma_tarihi", "guncelleme_tarihi")
    list_select_related = ("alici_firma",)
    readonly_fields = (
        "alici_firma",
        "olusturan",
        "olusturma_tarihi",
        "guncelleme_tarihi",
    )
    inlines = [CartLineInline]

    def get_queryset(self, request):
        return scope_cart_queryset(super().get_queryset(request), request.user)


@admin.register(CartLine)
class CartLineAdmin(_SiparisReadOnlyAdmin):
    list_display = (
        "id",
        "cart",
        "varyant",
        "miktar",
        "birim",
        "price_quote",
    )
    list_select_related = ("cart", "cart__alici_firma", "varyant", "price_quote")
    readonly_fields = [f.name for f in CartLine._meta.fields]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        cart_ids = scope_cart_queryset(
            Cart.objects.all(), request.user
        ).values_list("pk", flat=True)
        return qs.filter(cart_id__in=cart_ids)


@admin.register(CheckoutAttempt)
class CheckoutAttemptAdmin(_SiparisReadOnlyAdmin):
    list_display = (
        "id",
        "durum",
        "alici_firma",
        "idempotency_key",
        "olusturma_tarihi",
    )
    list_filter = ("durum",)
    list_select_related = ("alici_firma", "cart")
    readonly_fields = [f.name for f in CheckoutAttempt._meta.fields]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        from firmalar.services.yetki_servisi import can_view_all_tenants

        if can_view_all_tenants(request.user):
            return qs
        firma_id = getattr(request.user, "firma_id", None)
        if not firma_id:
            return qs.none()
        return qs.filter(alici_firma_id=firma_id)


class OrderLineInline(admin.TabularInline):
    model = OrderLine
    extra = 0
    can_delete = False
    fields = (
        "varyant",
        "miktar",
        "birim",
        "snapshot_satir_tutari_vergisiz",
        "para_birimi",
        "price_lock",
    )
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(_SiparisReadOnlyAdmin):
    list_display = (
        "id",
        "durum",
        "alici_firma",
        "idempotency_key",
        "olusturma_tarihi",
    )
    list_filter = ("durum",)
    list_select_related = ("alici_firma",)
    readonly_fields = [f.name for f in Order._meta.fields]
    inlines = [OrderLineInline]

    def get_queryset(self, request):
        from siparis.selectors.tenant import scope_order_queryset

        return scope_order_queryset(super().get_queryset(request), request.user)


@admin.register(OrderLine)
class OrderLineAdmin(_SiparisReadOnlyAdmin):
    list_display = (
        "id",
        "order",
        "varyant",
        "miktar",
        "birim",
        "snapshot_satir_tutari_vergisiz",
        "para_birimi",
    )
    list_select_related = ("order", "varyant", "price_lock")
    readonly_fields = [f.name for f in OrderLine._meta.fields]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        from firmalar.services.yetki_servisi import can_view_all_tenants

        if can_view_all_tenants(request.user):
            return qs
        firma_id = getattr(request.user, "firma_id", None)
        if not firma_id:
            return qs.none()
        return qs.filter(order__alici_firma_id=firma_id)
