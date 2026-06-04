import logging
import mimetypes
import os

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.http import FileResponse, Http404

from .models import (
    Program, NewsUpdate, SuccessStory,
    TeamMember, Milestone, ContactInquiry,
    ImpactReport, VolunteerApplication,
)

logger = logging.getLogger(__name__)

DEFAULT_MILESTONES = [
    {'year': 2009, 'title': 'PaaMoja Founded', 'description': 'Established in Mathare Valley focusing on youth education.'},
    {'year': 2012, 'title': 'DIYEP Program Launched', 'description': 'Expanded to 3 community centres.'},
    {'year': 2015, 'title': '100,000 Residents Reached', 'description': 'Touched over 100,000 lives across Mathare.'},
    {'year': 2018, 'title': 'JUMP! Partnership', 'description': 'Formal partnership expanding sports and leadership.'},
    {'year': 2021, 'title': 'Digital Transformation', 'description': 'Launched first digital platform post-COVID.'},
    {'year': 2026, 'title': '500,000+ Lives Reached', 'description': 'Cumulative community impact crosses half-million.'},
]

# ── CORE PAGES ────────────────────────────────────────────────────────────────
def home(request):
    programs = Program.objects.filter(is_active=True).order_by('order', 'title')
    news     = NewsUpdate.objects.filter(is_published=True).order_by('-date')[:3]
    stories  = SuccessStory.objects.filter(is_featured=True)
    return render(request, 'website/home.html', {'programs': programs, 'news': news, 'stories': stories})

def about(request):
    team       = TeamMember.objects.filter(is_active=True).order_by('order')
    milestones = Milestone.objects.all().order_by('year')
    return render(request, 'website/about.html', {'team': team, 'milestones': milestones, 'default_milestones': DEFAULT_MILESTONES})

def offline(request):
    return render(request, 'website/offline.html')

# ── CONTACT ───────────────────────────────────────────────────────────────────
def contact(request):
    if request.method == 'POST':
        name    = request.POST.get('name', '').strip()
        email   = request.POST.get('email', '').strip()
        phone   = request.POST.get('phone', '').strip()
        subject = request.POST.get('subject', 'general')
        message = request.POST.get('message', '').strip()

        errors = {}
        if not name: errors['name'] = 'Your name is required.'
        if not email or '@' not in email: errors['email'] = 'A valid email address is required.'
        if not message or len(message) < 10: errors['message'] = 'Please write a message (at least 10 characters).'

        if errors:
            return render(request, 'website/contact.html', {'errors': errors, 'form_data': request.POST})

        inquiry = ContactInquiry.objects.create(name=name, email=email, phone=phone, subject=subject, message=message)

        # Notify Team
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

        messages.success(request, f"Thank you, {name}! Your message has been received. We'll respond within 2 business days.")
        return redirect('website:contact')

    return render(request, 'website/contact.html')

# ── PROGRAMS ──────────────────────────────────────────────────────────────────
def program_list(request):
    programs = Program.objects.filter(is_active=True).order_by('order', 'title')
    return render(request, 'website/programs/program_list.html', {'programs': programs})

def program_detail(request, slug):
    program = get_object_or_404(Program, slug=slug, is_active=True)
    gallery = program.gallery.all().order_by('order')
    stories = SuccessStory.objects.filter(is_featured=True)[:3]
    other   = Program.objects.filter(is_active=True).exclude(pk=program.pk).order_by('order')[:3]
    return render(request, 'website/programs/program_detail.html', {
        'program': program, 'gallery': gallery, 'stories': stories, 'other_programs': other, 'volunteers_open': True,
    })

# ── IMPACT REPORTS ────────────────────────────────────────────────────────────
def impact_reports(request):
    report_type = request.GET.get('type', '')
    year        = request.GET.get('year', '')
    reports     = ImpactReport.objects.filter(is_published=True)

    if report_type: reports = reports.filter(report_type=report_type)
    if year:        reports = reports.filter(year=year)

    years = ImpactReport.objects.filter(is_published=True).values_list('year', flat=True).distinct().order_by('-year')
    return render(request, 'website/impact_reports.html', {
        'reports': reports, 'years': years, 'report_types': ImpactReport.REPORT_TYPE_CHOICES,
        'active_type': report_type, 'active_year': year,
    })

def download_report(request, pk):
    report = get_object_or_404(ImpactReport, pk=pk, is_published=True)
    if not report.file: raise Http404("Report file not found.")
    try:
        file_path = report.file.path
        if not os.path.exists(file_path): raise Http404("Report file not found on disk.")
        ImpactReport.objects.filter(pk=pk).update(downloads=report.downloads + 1)
        content_type, _ = mimetypes.guess_type(file_path)
        return FileResponse(
            open(file_path, 'rb'), 
            content_type=content_type or 'application/octet-stream', 
            as_attachment=True, 
            filename=f"PaaMoja_{report.year}_{report.title.replace(' ', '_')}.pdf"
        )
    except Exception as e:
        logger.error(f"Report download failed for Report #{pk}: {e}")
        raise Http404("Could not serve this file. Please contact us.")

# ── VOLUNTEER ─────────────────────────────────────────────────────────────────
def volunteer(request):
    programs = Program.objects.filter(is_active=True).order_by('order')

    if request.method == 'POST':
        full_name      = request.POST.get('full_name', '').strip()
        email          = request.POST.get('email', '').strip()
        phone          = request.POST.get('phone', '').strip()
        location       = request.POST.get('location', '').strip()
        age_raw        = request.POST.get('age', '').strip()
        program_id     = request.POST.get('program', '')
        skills         = request.POST.get('skills', '').strip()
        motivation     = request.POST.get('motivation', '').strip()
        availability   = request.POST.get('availability', 'weekends')
        commitment     = request.POST.get('commitment', 'monthly')
        has_experience = request.POST.get('has_experience') == 'on'

        errors = {}
        if not full_name: errors['full_name'] = 'Your full name is required.'
        if not email or '@' not in email: errors['email'] = 'A valid email address is required.'
        if not phone: errors['phone'] = 'A phone number is required.'
        if not skills or len(skills) < 10: errors['skills'] = 'Please describe your skills (at least 10 characters).'
        if not motivation or len(motivation) < 20: errors['motivation'] = 'Please share your motivation (at least 20 characters).'

        age = None
        if age_raw:
            try:
                age = int(age_raw)
                if not (13 <= age <= 80): errors['age'] = 'Please enter a valid age (13–80).'
            except ValueError:
                errors['age'] = 'Age must be a number.'

        program_obj = None
        if program_id:
            try: program_obj = Program.objects.get(pk=program_id, is_active=True)
            except Program.DoesNotExist: pass

        if errors:
            return render(request, 'website/volunteer.html', {
                'errors': errors, 'form_data': request.POST, 'programs': programs,
            })

        application = VolunteerApplication.objects.create(
            full_name=full_name, email=email, phone=phone, location=location, age=age,
            program=program_obj, skills=skills, motivation=motivation,
            availability=availability, commitment=commitment, has_experience=has_experience,
        )

        # Notify Team
        try:
            team_body = render_to_string('website/emails/volunteer_team.txt', {'app': application})
            send_mail(
                subject=f"[PaaMoja Volunteer] New application — {application.full_name}",
                message=team_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=['info@paamoja.org'],
                fail_silently=True,
            )
        except Exception as e:
            logger.error(f"Volunteer team email failed: {e}")

        # Auto-reply
        try:
            auto_body = render_to_string('website/emails/volunteer_autoreply.txt', {'app': application})
            send_mail(
                subject="Your volunteer application — PaaMoja Initiative",
                message=auto_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[application.email],
                fail_silently=True,
            )
        except Exception as e:
            logger.warning(f"Volunteer auto-reply failed: {e}")

        messages.success(request, f"Thank you, {full_name}! Your volunteer application has been received. We'll be in touch within 5 business days.")
        return redirect('website:volunteer')

    return render(request, 'website/volunteer.html', {'programs': programs})