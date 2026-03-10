from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('phone', 'role', 'accepted_privacy_policy', 'is_staff', 'is_superuser', 'created_at')
    list_filter = ('role', 'is_staff', 'is_superuser', 'accepted_privacy_policy')
    search_fields = ('phone',)
    ordering = ('created_at',)
    readonly_fields = ('created_at', 'updated_at', 'last_login')  # ✅ non-éditables
    fieldsets = (
        (None, {'fields': ('phone', 'password')}),
        ('Permissions', {'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Infos personnelles', {'fields': ('role', 'accepted_privacy_policy')}),
        ('Dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone', 'password1', 'password2', 'role', 'accepted_privacy_policy', 'is_staff', 'is_superuser')}
        ),
    )