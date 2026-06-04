"""
Add these views to website/views.py
Also add these URL patterns to website/urls.py:

    path('newsletter/subscribe/',         views.newsletter_subscribe,   name='newsletter_subscribe'),
    path('newsletter/unsubscribe/<token>/',views.newsletter_unsubscribe, name='newsletter_unsubscribe'),
"""

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from .models import NewsletterSubscriber
import logging

logger = logging.getLogger(__name__)


@require_POST
def newsletter_subscribe(request):
    """
    POST /newsletter/subscribe/
    Accepts both AJAX (JSON response) and regular form POST (redirect).
    Body: email, first_name (optional), source (optional)
    """
    email      = request.POST.get('email', '').strip().lower()
    first_name = request.POST.get('first_name', '').strip()[:60]
    source     = request.POST.get('source', 'homepage')
    is_ajax    = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if not email or '@' not in email:
        if is_ajax:
            return JsonResponse({'success': False, 'error': 'Please enter a valid email address.'}, status=400)
        from django.contrib import messages
        messages.error(request, 'Please enter a valid email address.')
        return _redirect_back(request)

    subscriber, created = NewsletterSubscriber.objects.get_or_create(
        email=email,
        defaults={'first_name': first_name, 'source': source, 'is_active': True},
    )

    if not created:
        if not subscriber.is_active:
            # Re-subscribe
            subscriber.is_active       = True
            subscriber.unsubscribed_at = None
            subscriber.save(update_fields=['is_active', 'unsubscribed_at'])
            msg = "Welcome back! You've been re-subscribed to PaaMoja updates."
        else:
            msg = "You're already subscribed — we'll keep the updates coming!"
    else:
        msg = "Thank you! You're now subscribed to PaaMoja Initiative updates."
        _send_welcome_email(subscriber)
        logger.info(f"New newsletter subscriber: {email} via {source}")

    if is_ajax:
        return JsonResponse({'success': True, 'message': msg})

    from django.contrib import messages
    messages.success(request, msg)
    return _redirect_back(request)


def newsletter_unsubscribe(request, token):
    """GET /newsletter/unsubscribe/<token>/"""
    subscriber = get_object_or_404(NewsletterSubscriber, unsubscribe_token=token)

    if subscriber.is_active:
        subscriber.is_active       = False
        subscriber.unsubscribed_at = timezone.now()
        subscriber.save(update_fields=['is_active', 'unsubscribed_at'])
        unsubscribed = True
    else:
        unsubscribed = False  # already inactive

    return render(request, 'website/newsletter_unsubscribe.html', {
        'subscriber':   subscriber,
        'unsubscribed': unsubscribed,
    })


def _redirect_back(request):
    from django.shortcuts import redirect
    referer = request.META.get('HTTP_REFERER', '/')
    return redirect(referer)


def _send_welcome_email(subscriber):
    try:
        from django.core.mail import send_mail
        from django.conf import settings
        name = subscriber.first_name or 'Friend'
        send_mail(
            subject    = "Welcome to PaaMoja Initiative Updates 🌟",
            message    = (
                f"Dear {name},\n\n"
                f"Thank you for subscribing to PaaMoja Initiative's newsletter!\n\n"
                f"You'll receive updates about our programs, community impact stories, "
                f"and ways to get involved in Mathare Valley.\n\n"
                f"To unsubscribe at any time, visit:\n"
                f"https://paamoja.org/newsletter/unsubscribe/{subscriber.unsubscribe_token}/\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"PaaMoja Initiative | Mathare Valley, Nairobi\n"
                f"info@paamoja.org | +254 712 244 204\n"
                f"\"Follow. Learn. Lead.\""
            ),
            from_email     = f"PaaMoja Initiative <{settings.DEFAULT_FROM_EMAIL}>",
            recipient_list = [subscriber.email],
            fail_silently  = True,
        )
    except Exception as e:
        logger.warning(f"Newsletter welcome email failed for {subscriber.email}: {e}")