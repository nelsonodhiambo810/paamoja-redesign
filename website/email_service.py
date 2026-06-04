"""
PaaMoja Email Service — Sprint 2 Final
───────────────────────────────────────
All outbound emails go through here.
Receipt now routes to donor_email if provided, falls back to team inbox.
receipt_sent flag is set on the Donation record after successful dispatch.
"""

import logging
from decimal import Decimal
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


# ── Tiered impact statements ───────────────────────────────────────────────────

def _get_impact_statement(amount: Decimal) -> str:
    n = int(amount)

    if n < 500:
        return (
            f"Your KES {n:,} contribution covers daily stationery and supplies "
            f"that keep our Mathare youth programs running. No amount is too small — "
            f"every shilling builds a stronger community."
        )
    elif n < 1000:
        return (
            f"Your KES {n:,} donation funds a full week of program materials for "
            f"a young person in our DIYEP life skills sessions — giving them "
            f"knowledge that will last a lifetime."
        )
    elif n < 2500:
        return (
            f"Your KES {n:,} gift can fund an entire community workshop in Mathare "
            f"Valley — bringing together 20+ youth for a day of learning, leadership "
            f"training, and peer mentorship."
        )
    elif n < 5000:
        return (
            f"Your KES {n:,} contribution can fully sponsor a young person through "
            f"one complete module of our DIYEP sexuality and life skills program — "
            f"changing how they see themselves and their future."
        )
    elif n < 10000:
        return (
            f"Your extraordinary KES {n:,} donation funds an entire week of "
            f"programming across multiple PaaMoja community centres — reaching "
            f"hundreds of young people across Mathare Valley."
        )
    else:
        return (
            f"Your remarkable KES {n:,} contribution places you among our most "
            f"impactful supporters. A gift of this size sustains a full month of "
            f"community programming — directly transforming the lives of Mathare's "
            f"youth and their families."
        )


def _format_phone(phone: str) -> str:
    """254712XXXXXX → +254 712 XXX XXX"""
    digits = phone.replace('+', '').replace(' ', '')
    if len(digits) == 12 and digits.startswith('254'):
        return f"+{digits[:3]} {digits[3:6]} {digits[6:9]} {digits[9:]}"
    return phone


def _resolve_recipient(donation) -> str | None:
    email = getattr(donation, 'donor_email', '').strip()
    if email and '@' in email:
        return email
    return None


# ── Public API ─────────────────────────────────────────────────────────────────

def send_donation_receipt(donation) -> bool:
    """
    Send the HTML + plain-text receipt to the donor.
    BCC copy always goes to team inbox for records.
    Sets donation.receipt_sent = True on success.
    """
    if not donation.mpesa_receipt:
        logger.error(
            f"Donation #{donation.id} has no receipt number — skipping."
        )
        return False

    donor_email = _resolve_recipient(donation)
    donor_name  = (getattr(donation, 'donor_name', '') or 'Valued Supporter').strip()

    if not donor_email:
        logger.warning(
            f"Donation #{donation.id} has no donor_email — "
            f"receipt will go to team inbox only."
        )

    context = {
        'donor_name':       donor_name,
        'amount':           donation.amount,
        'mpesa_receipt':    donation.mpesa_receipt,
        'phone_number':     _format_phone(donation.phone_number),
        'transaction_date': timezone.localtime(donation.updated_at).strftime(
                                '%B %d, %Y at %I:%M %p EAT'
                            ),
        'impact_statement': _get_impact_statement(donation.amount),
    }

    subject = (
        f"Your Donation Receipt — KES {int(donation.amount):,} "
        f"| PaaMoja Initiative [Ref: {donation.mpesa_receipt}]"
    )

    try:
        html_body = render_to_string('website/emails/donation_receipt.html', context)
        text_body = render_to_string('website/emails/donation_receipt.txt',  context)
    except Exception as e:
        logger.exception(f"Template render failed for Donation #{donation.id}: {e}")
        return False

    to_list  = [donor_email] if donor_email else [settings.DEFAULT_FROM_EMAIL]
    bcc_list = [settings.DEFAULT_FROM_EMAIL] if donor_email else []

    if not donor_email:
        subject = f"[NO DONOR EMAIL] {subject}"

    email_msg = EmailMultiAlternatives(
        subject    = subject,
        body       = text_body,
        from_email = f"PaaMoja Initiative <{settings.DEFAULT_FROM_EMAIL}>",
        to         = to_list,
        bcc        = bcc_list,
        reply_to   = ['info@paamoja.org'],
    )
    email_msg.attach_alternative(html_body, "text/html")

    try:
        email_msg.send(fail_silently=False)
        donation.receipt_sent = True
        donation.save(update_fields=['receipt_sent'])
        logger.info(
            f"Receipt sent | Donation #{donation.id} | "
            f"KES {donation.amount} | {donation.mpesa_receipt} | To: {to_list}"
        )
        return True
    except Exception as e:
        logger.error(f"Receipt FAILED | Donation #{donation.id} | {e}")
        return False


def send_donation_alert_to_team(donation) -> bool:
    """Quick internal alert to team inbox on every successful donation."""
    donor_label = (
        f"{donation.donor_name} <{donation.donor_email}>"
        if getattr(donation, 'donor_email', '') else donation.phone_number
    )
    subject = f"💛 New Donation: KES {int(donation.amount):,} from {donor_label}"
    body = (
        f"A donation has been confirmed on paamoja.org.\n\n"
        f"  Donor    : {getattr(donation, 'donor_name', '') or 'Unknown'}\n"
        f"  Email    : {getattr(donation, 'donor_email', '') or 'Not provided'}\n"
        f"  Phone    : {_format_phone(donation.phone_number)}\n"
        f"  Amount   : KES {int(donation.amount):,}\n"
        f"  Receipt  : {donation.mpesa_receipt}\n"
        f"  Time     : {timezone.localtime(donation.updated_at).strftime('%B %d, %Y at %I:%M %p EAT')}\n\n"
        f"CMS: {getattr(settings, 'SITE_URL', 'https://paamoja.org')}"
        f"/admin/website/donation/{donation.id}/change/\n\n"
        f"-- PaaMoja Automated System"
    )
    try:
        from django.core.mail import send_mail
        send_mail(
            subject        = subject,
            message        = body,
            from_email     = settings.DEFAULT_FROM_EMAIL,
            recipient_list = ['info@paamoja.org'],
            fail_silently  = True,
        )
        logger.info(f"Team alert sent | Donation #{donation.id}")
        return True
    except Exception as e:
        logger.warning(f"Team alert FAILED | Donation #{donation.id} | {e}")
        return False