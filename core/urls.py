from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # This points to your newly created website/urls.py
    path('', include('website.urls', namespace='website')),
    
    # This points to your new Daraja integration in mpesa/urls.py
    path('mpesa/', include('mpesa.urls', namespace='mpesa')),
]

# Serve media files locally during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)