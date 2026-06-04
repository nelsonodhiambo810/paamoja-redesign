"""
Add to core/urls.py — SEO sitemap + robots.txt

pip install django-sitemaps  (already included in Django)
No extra install needed.
"""

# ── core/urls.py — final version ──────────────────────────────────────────────

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from django.views.generic import TemplateView

from website.sitemaps import (
    StaticViewSitemap,
    ProgramSitemap,
    ImpactReportSitemap,
)
from website.admin_dashboard import admin_dashboard
from website.views import offline

urlpatterns = [
    # Dashboard (must be before admin/ to avoid URL conflict)
    path('admin/dashboard/', admin_dashboard, name='admin_dashboard'),
    path('admin/', admin.site.urls),

    # Main website
    path('', include('website.urls', namespace='website')),

    # M-Pesa
    path('mpesa/', include('mpesa.urls', namespace='mpesa')),

    # SEO
    path('sitemap.xml', sitemap, {'sitemaps': {
        'static':   StaticViewSitemap,
        'programs': ProgramSitemap,
        'reports':  ImpactReportSitemap,
    }}, name='django.contrib.sitemaps.views.sitemap'),

    path('robots.txt', TemplateView.as_view(
        template_name='website/robots.txt',
        content_type='text/plain',
    ), name='robots_txt'),

    # PWA offline fallback
    path('offline/', offline, name='offline'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)