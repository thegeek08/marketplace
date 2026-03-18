from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils import timezone
from django.utils.html import format_html
from .models import User, SubscriptionRequest


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('phone', 'nom', 'role', 'plan_badge', 'plan_expires_at', 'is_staff', 'created_at')
    list_filter = ('role', 'plan', 'is_staff', 'is_superuser', 'accepted_privacy_policy')
    search_fields = ('phone', 'nom')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'last_login')
    fieldsets = (
        (None, {'fields': ('phone', 'password')}),
        ('Permissions', {'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Infos personnelles', {'fields': ('role', 'nom', 'email', 'accepted_privacy_policy', 'phone_verified', 'profile_completed')}),
        ('Abonnement', {'fields': ('plan', 'plan_expires_at')}),
        ('Dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone', 'password1', 'password2', 'role', 'accepted_privacy_policy', 'is_staff', 'is_superuser')}
        ),
    )

    @admin.display(description='Plan', ordering='plan')
    def plan_badge(self, obj):
        colors = {'gratuit': '#6c757d', 'standard': '#0d6efd', 'pro': '#ffc107'}
        color = colors.get(obj.plan, '#6c757d')
        label = obj.get_plan_display()
        actif = obj.plan_actif()
        if obj.plan != 'gratuit' and actif == 'gratuit':
            return format_html('<span style="color:#dc3545;font-weight:bold">⚠️ Expiré</span>')
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:10px;font-size:12px">{}</span>',
            color, label
        )


@admin.register(SubscriptionRequest)
class SubscriptionRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan_demande', 'moyen_paiement', 'numero_transaction',
                    'duree_mois', 'statut_badge', 'created_at', 'actions_rapides')
    list_filter = ('statut', 'plan_demande', 'moyen_paiement')
    search_fields = ('user__phone', 'user__nom', 'numero_transaction')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'traite_le', 'user')
    actions = ['approuver_selections', 'refuser_selections']

    fieldsets = (
        ('Demande', {'fields': ('user', 'plan_demande', 'moyen_paiement', 'numero_transaction', 'duree_mois')}),
        ('Traitement', {'fields': ('statut', 'note_admin', 'traite_le', 'created_at')}),
    )

    @admin.display(description='Statut')
    def statut_badge(self, obj):
        styles = {
            'en_attente': 'background:#ffc107;color:#212529',
            'approuvee':  'background:#198754;color:white',
            'refusee':    'background:#dc3545;color:white',
        }
        style = styles.get(obj.statut, '')
        return format_html(
            '<span style="{};padding:2px 10px;border-radius:10px;font-size:12px">{}</span>',
            style, obj.get_statut_display()
        )

    @admin.display(description='Actions')
    def actions_rapides(self, obj):
        if obj.statut == 'en_attente':
            return format_html(
                '<a href="../{}/change/" style="color:#198754;font-weight:bold">✔ Traiter</a>',
                obj.pk
            )
        return '—'

    @admin.action(description='✔ Approuver les demandes sélectionnées')
    def approuver_selections(self, request, queryset):
        count = 0
        for req in queryset.filter(statut='en_attente'):
            req.approuver()
            count += 1
        self.message_user(request, f"{count} demande(s) approuvée(s) — plans activés.")

    @admin.action(description='✘ Refuser les demandes sélectionnées')
    def refuser_selections(self, request, queryset):
        count = queryset.filter(statut='en_attente').update(
            statut='refusee', traite_le=timezone.now()
        )
        self.message_user(request, f"{count} demande(s) refusée(s).")

    def save_model(self, request, obj, form, change):
        """Approuve automatiquement si le statut passe à 'approuvee'."""
        if change:
            old = SubscriptionRequest.objects.get(pk=obj.pk)
            if old.statut != 'approuvee' and obj.statut == 'approuvee':
                obj.approuver()
                return
            if old.statut != 'refusee' and obj.statut == 'refusee':
                obj.traite_le = timezone.now()
        super().save_model(request, obj, form, change)
