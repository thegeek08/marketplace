from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from products import views as product_views

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
    # PWA
    path('sw.js', TemplateView.as_view(
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