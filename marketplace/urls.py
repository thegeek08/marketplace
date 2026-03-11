from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from products import views as product_views


class NoCacheTemplateView(TemplateView):
    """TemplateView avec Cache-Control: no-cache, no-store pour le Service Worker.
    Indispensable pour que le navigateur détecte immédiatement les mises à jour
    du SW sans attendre l'expiration du cache HTTP (qui peut durer 24h par défaut).
    """
    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response


urlpatterns = [
    path('', product_views.home, name='home'),
    path('gestion-secure-panel/', admin.site.urls),  # URL non prévisible pour l'admin
    path('products/', include('products.urls')),
    path('users/', include('users.urls')),
    path('users/', include('django.contrib.auth.urls')),
    path('cart/', include('cart.urls')),
    path('orders/', include('orders.urls')),
    path('messaging/', include('messaging.urls')),
    path('favorites/', include('favorites.urls')),
    path('notifications/', include('notifications.urls')),
    # PWA — sw.js servi sans cache HTTP pour détecter les mises à jour immédiatement
    path('sw.js', NoCacheTemplateView.as_view(
        template_name='pwa/sw.js',
        content_type='application/javascript',
        extra_context={'app_version': settings.APP_VERSION},
    ), name='service_worker'),
    path('offline/', TemplateView.as_view(
        template_name='pwa/offline.html',
    ), name='offline'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)