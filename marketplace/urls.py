from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from products import views as product_views

urlpatterns = [
    path('', product_views.home, name='home'),
    path('admin/', admin.site.urls),
    path('products/', include('products.urls')),
    path('users/', include('users.urls')),
    path('users/', include('django.contrib.auth.urls')),
    path('cart/', include('cart.urls')),
    path('orders/', include('orders.urls')),
    path('messaging/', include('messaging.urls')),
    path('favorites/', include('favorites.urls')),
    path('notifications/', include('notifications.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)