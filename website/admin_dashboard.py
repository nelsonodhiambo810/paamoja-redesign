"""
Custom Django admin dashboard view.
Replaces the default Jazzmin index with a live stats dashboard.

Steps to wire up:
1. Add this file at:  website/admin_dashboard.py
2. Add to core/urls.py (see bottom of this file)
3. Add JAZZMIN_SETTINGS key to core/settings/base.py (see bottom)
"""

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Sum, Count
from datetime import timedelta

from website.models import (
    Program, NewsUpdate, SuccessStory,
    ContactInquiry, ImpactReport,
    VolunteerApplication, Donation,
    NewsletterSubscriber,
)


@staff_member_required
def admin_dashboard(request):
    now   = timezone.now()
    today = now.date()
    week_ago  = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    # ── Donations ─────────────────────────────────────────────────────────────
    total_donations_kes = (
        Donation.objects.filter(status='success')
        .aggregate(total=Sum('amount'))['total'] or 0
    )
    donations_this_month = (
        Donation.objects.filter(status='success', created_at__gte=month_ago)
        .aggregate(total=Sum('amount'))['total'] or 0
    )
    donations_this_week = (
        Donation.objects.filter(status='success', created_at__gte=week_ago)
        .aggregate(total=Sum('amount'))['total'] or 0
    )
    recent_donations = (
        Donation.objects.filter(status='success')
        .order_by('-created_at')[:5]
    )
    donation_count_total = Donation.objects.filter(status='success').count()

    # ── Volunteers ────────────────────────────────────────────────────────────
    volunteer_total      = VolunteerApplication.objects.count()
    volunteer_pending    = VolunteerApplication.objects.filter(status='pending').count()
    volunteer_accepted   = VolunteerApplication.objects.filter(status='accepted').count()
    volunteer_this_month = VolunteerApplication.objects.filter(created_at__gte=month_ago).count()
    recent_volunteers    = VolunteerApplication.objects.order_by('-created_at')[:5]

    # ── Newsletter ────────────────────────────────────────────────────────────
    newsletter_total      = NewsletterSubscriber.objects.filter(is_active=True).count()
    newsletter_this_month = NewsletterSubscriber.objects.filter(
        is_active=True, subscribed_at__gte=month_ago
    ).count()
    newsletter_this_week  = NewsletterSubscriber.objects.filter(
        is_active=True, subscribed_at__gte=week_ago
    ).count()

    # ── Contact Inquiries ─────────────────────────────────────────────────────
    inquiries_new   = ContactInquiry.objects.filter(status='new').count()
    recent_inquiries = ContactInquiry.objects.order_by('-created_at')[:5]

    # ── Content stats ─────────────────────────────────────────────────────────
    programs_active   = Program.objects.filter(is_active=True).count()
    reports_published = ImpactReport.objects.filter(is_published=True).count()
    report_downloads  = (
        ImpactReport.objects.aggregate(total=Sum('downloads'))['total'] or 0
    )
    stories_total     = SuccessStory.objects.filter(is_featured=True).count()

    # ── Daily donation sparkline (last 7 days) ─────────────────────────────
    sparkline = []
    for i in range(6, -1, -1):
        day   = today - timedelta(days=i)
        total = (
            Donation.objects
            .filter(status='success', created_at__date=day)
            .aggregate(t=Sum('amount'))['t'] or 0
        )
        sparkline.append({'day': day.strftime('%a'), 'total': int(total)})

    context = {
        # Donations
        'total_donations_kes':  total_donations_kes,
        'donations_this_month': donations_this_month,
        'donations_this_week':  donations_this_week,
        'donation_count_total': donation_count_total,
        'recent_donations':     recent_donations,
        'sparkline':            sparkline,
        'sparkline_max':        max((s['total'] for s in sparkline), default=1) or 1,

        # Volunteers
        'volunteer_total':      volunteer_total,
        'volunteer_pending':    volunteer_pending,
        'volunteer_accepted':   volunteer_accepted,
        'volunteer_this_month': volunteer_this_month,
        'recent_volunteers':    recent_volunteers,

        # Newsletter
        'newsletter_total':      newsletter_total,
        'newsletter_this_month': newsletter_this_month,
        'newsletter_this_week':  newsletter_this_week,

        # Inquiries
        'inquiries_new':   inquiries_new,
        'recent_inquiries': recent_inquiries,

        # Content
        'programs_active':   programs_active,
        'reports_published': reports_published,
        'report_downloads':  report_downloads,
        'stories_total':     stories_total,

        # Time
        'now': now,
    }

    return render(request, 'admin/dashboard.html', context)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ADD TO core/urls.py — insert ABOVE the admin/ path:
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
#   from website.admin_dashboard import admin_dashboard
#
#   urlpatterns = [
#       path('admin/dashboard/', admin_dashboard, name='admin_dashboard'),
#       path('admin/', admin.site.urls),
#       ...
#   ]
#
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ADD TO core/settings/base.py JAZZMIN_SETTINGS dict:
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
#   "custom_links": {
#       "website": [{
#           "name": "📊 Live Dashboard",
#           "url": "/admin/dashboard/",
#           "icon": "fas fa-chart-line",
#       }]
#   },
#
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━