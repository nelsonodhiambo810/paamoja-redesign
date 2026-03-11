from django.contrib import admin
from django.urls import path
from website.views import home
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # This is the line that went missing! It tells Django where the admin panel lives.
    path('admin/', admin.site.urls), 
    
    # This points the blank URL (the homepage) to your home view
    path('', home, name='home'), 
]

# This allows your uploaded images (like the Success Stories) to load properly
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)