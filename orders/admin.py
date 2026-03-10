from django.contrib import admin
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
    list_display = ('pk', 'client', 'status', 'total', 'payment_method', 'created_at')
    list_filter = ('status', 'payment_method')
    search_fields = ('client__phone', 'client__nom')
    inlines = [OrderItemInline, OrderStatusHistoryInline]


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('order', 'status', 'changed_by', 'created_at')
    list_filter = ('status',)
