from django.contrib import admin
from .models import Product, Category, Rating


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon', 'description')
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'seller', 'created_at')
    list_filter = ('category',)
    search_fields = ('name', 'description')


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('product', 'client', 'score', 'created_at')
    list_filter = ('score',)