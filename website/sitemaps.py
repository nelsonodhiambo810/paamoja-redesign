"""
website/sitemaps.py
Auto-generates /sitemap.xml for Google Search Console.
Add 'django.contrib.sitemaps' to INSTALLED_APPS in base.py.
"""

from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Program, ImpactReport


class StaticViewSitemap(Sitemap):
    priority   = 0.8
    changefreq = 'weekly'
    protocol   = 'https'

    def items(self):
        return [
            'website:home',
            'website:about',
            'website:contact',
            'website:volunteer',
            'website:program_list',
            'website:impact_reports',
        ]

    def location(self, item):
        return reverse(item)


class ProgramSitemap(Sitemap):
    priority   = 0.9
    changefreq = 'monthly'
    protocol   = 'https'

    def items(self):
        return Program.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return obj.get_absolute_url()


class ImpactReportSitemap(Sitemap):
    priority   = 0.6
    changefreq = 'yearly'
    protocol   = 'https'

    def items(self):
        return ImpactReport.objects.filter(is_published=True)

    def lastmod(self, obj):
        return obj.created_at