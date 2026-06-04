"""
Add these paths to website/urls.py
"""

# Add these imports at the top of website/urls.py:
#   from .newsletter_views import newsletter_subscribe, newsletter_unsubscribe
#   from .views import offline

# Add these paths to urlpatterns:

from django.urls import path
from . import views
from .newsletter_views import newsletter_subscribe, newsletter_unsubscribe

app_name = 'website'

urlpatterns = [
    # Core pages
    path('',                     views.home,           name='home'),
    path('about/',               views.about,          name='about'),
    path('contact/',             views.contact,        name='contact'),
    path('volunteer/',           views.volunteer,      name='volunteer'),
    path('offline/',             views.offline,        name='offline'),

    # Programs
    path('programs/',            views.program_list,   name='program_list'),
    path('programs/<slug:slug>/',views.program_detail, name='program_detail'),

    # Impact Reports
    path('impact-reports/',                   views.impact_reports,  name='impact_reports'),
    path('impact-reports/<int:pk>/download/', views.download_report, name='download_report'),

    # Newsletter
    path('newsletter/subscribe/',              newsletter_subscribe,             name='newsletter_subscribe'),
    path('newsletter/unsubscribe/<str:token>/',newsletter_unsubscribe,           name='newsletter_unsubscribe'),
]