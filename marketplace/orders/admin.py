from django.contrib import admin
from django.db.models import Sum
from django.utils.html import format_html
from .models import Order, OrderItem, OrderStatusHistory


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'price')


class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ('status', 'changed_by', 'note', 'created_at')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'pk', 'client', 'status', 'total',
        'commission_rate_display', 'commission_amount', 'vendor_amount_display',
        'payment_method', 'created_at'
    )
    list_filter = ('status', 'payment_method')
    search_fields = ('client__phone', 'client__nom')
    readonly_fields = ('commission_amount', 'vendor_amount_display')
    inlines = [OrderItemInline, OrderStatusHistoryInline]

    def commission_rate_display(self, obj):
        return f"{obj.commission_rate} %"
    commission_rate_display.short_description = "Taux"

    def vendor_amount_display(self, obj):
        return f"{obj.vendor_amount} FCFA"
    vendor_amount_display.short_description = "Reversé vendeur"

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        qs = self.get_queryset(request).filter(status='livree')
        totals = qs.aggregate(
            total_revenus=Sum('commission_amount'),
            total_ventes=Sum('total'),
        )
        extra_context['total_commissions'] = totals['total_revenus'] or 0
        extra_context['total_ventes'] = totals['total_ventes'] or 0
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('order', 'status', 'changed_by', 'created_at')
    list_filter = ('status',)
