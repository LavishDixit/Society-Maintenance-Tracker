from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path

urlpatterns = [
    path('', lambda request: redirect('accounts:login')),
    path('admin-panel/', admin.site.urls),  # Django's built-in admin, kept separate from our /admin/ app views
    path('accounts/', include('accounts.urls')),
    path('complaints/', include('complaints.urls')),
    path('notices/', include('notices.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('community/', include('community.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
