"""
PaaMoja Website Views — Sprint 1 Complete
"""

import logging
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

from .models import (
    Program, NewsUpdate, SuccessStory,
    TeamMember, Milestone, ContactInquiry,
)

logger = logging.getLogger(__name__)

# ── Default milestone data shown before CMS is populated ──────────────────────
DEFAULT_MILESTONES = [
    {'year': 2009, 'title': 'PaaMoja Founded',
     'description': 'The initiative was established in Mathare Valley with a focus on youth sexuality education.'},
    {'year': 2012, 'title': 'DIYEP Program Launched',
     'description': 'The Dialogue Initiative for Youth Empowerment Program expanded to 3 community centres.'},
    {'year': 2015, 'title': '100,000 Residents Reached',
     'description': 'A major milestone — PaaMoja\'s programs touched over 100,000 lives across Mathare.'},
    {'year': 2018, 'title': 'JUMP! Partnership',
     'description': 'Formal partnership signed with JUMP! expanding sports and leadership programming.'},
    {'year': 2021, 'title': 'Digital Transformation',
     'description': 'PaaMoja launched its first digital platform to reach youth online post-COVID.'},
    {'year': 2026, 'title': '500,000+ Lives Reached',
     'description': 'PaaMoja\'s cumulative community impact crosses the half-million mark.'},
]


def home(request):
    programs   = Program.objects.filter(is_active=True).order_by('order', 'title')
    news       = NewsUpdate.objects.filter(is_published=True).order_by('-date')[:3]
    stories    = SuccessStory.objects.filter(is_featured=True)

    return render(request, 'website/home.html', {
        'programs': programs,
        'news':     news,
        'stories':  stories,
    })


def about(request):
    team       = TeamMember.objects.filter(is_active=True).order_by('order')
    milestones = Milestone.objects.all().order_by('year')

    return render(request, 'website/about.html', {
        'team':               team,
        'milestones':         milestones,
        'default_milestones': DEFAULT_MILESTONES,
    })


def contact(request):
    if request.method == 'POST':
        name    = request.POST.get('name',    '').strip()
        email   = request.POST.get('email',   '').strip()
        phone   = request.POST.get('phone',   '').strip()
        subject = request.POST.get('subject', 'general')
        message = request.POST.get('message', '').strip()

        # Validation
        errors = {}
        if not name:
            errors['name'] = 'Your name is required.'
        if not email or '@' not in email:
            errors['email'] = 'A valid email address is required.'
        if not message or len(message) < 10:
            errors['message'] = 'Please write a message (at least 10 characters).'

        if errors:
            return render(request, 'website/contact.html', {
                'errors':    errors,
                'form_data': request.POST,
            })

        # Save to database
        inquiry = ContactInquiry.objects.create(
            name=name, email=email, phone=phone,
            subject=subject, message=message,
        )

        # Email team
        try:
            team_body = render_to_string('website/emails/contact_team.txt', {'inquiry': inquiry})
            send_mail(
                subject=f"[PaaMoja Contact] {inquiry.get_subject_display()} — {name}",
                message=team_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=['info@paamoja.org'],
                fail_silently=False,
            )
        except Exception as e:
            logger.error(f"Team contact email failed: {e}")

        # Auto-reply to sender
        try:
            sender_body = render_to_string('website/emails/contact_autoreply.txt', {'name': name})
            send_mail(
                subject="Thank you for reaching out — PaaMoja Initiative",
                message=sender_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=True,
            )
        except Exception as e:
            logger.warning(f"Auto-reply failed: {e}")

        messages.success(request,
            f"Thank you, {name}! Your message has been received. We'll respond within 2 business days.")
        return redirect('website:contact')

    return render(request, 'website/contact.html')