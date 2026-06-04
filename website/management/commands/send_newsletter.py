"""
Management command to send a newsletter broadcast to all active subscribers.

Usage:
    python manage.py send_newsletter --subject "May Update" --body-file newsletter_may.txt
    python manage.py send_newsletter --subject "May Update" --body "Hello everyone, ..."
    python manage.py send_newsletter --subject "May Update" --body-file may.txt --dry-run

Place this file at:
    website/management/__init__.py        (empty file)
    website/management/commands/__init__.py (empty file)
    website/management/commands/send_newsletter.py (this file)
"""

from django.core.management.base import BaseCommand, CommandError
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from website.models import NewsletterSubscriber
import time


class Command(BaseCommand):
    help = 'Send a newsletter broadcast to all active subscribers.'

    def add_arguments(self, parser):
        parser.add_argument('--subject',   required=True, help='Email subject line')
        parser.add_argument('--body',      help='Plain text body (inline)')
        parser.add_argument('--body-file', help='Path to a .txt file containing the body')
        parser.add_argument('--dry-run',   action='store_true',
                            help='Print what would be sent without actually sending')
        parser.add_argument('--delay',     type=float, default=0.1,
                            help='Seconds between emails to avoid rate limiting (default: 0.1)')

    def handle(self, *args, **options):
        subject   = options['subject']
        dry_run   = options['dry_run']
        delay     = options['delay']

        # Resolve body text
        if options.get('body_file'):
            try:
                with open(options['body_file'], 'r', encoding='utf-8') as f:
                    body = f.read()
            except FileNotFoundError:
                raise CommandError(f"Body file not found: {options['body_file']}")
        elif options.get('body'):
            body = options['body']
        else:
            raise CommandError("Provide either --body or --body-file.")

        subscribers = NewsletterSubscriber.objects.filter(is_active=True)
        count = subscribers.count()

        if count == 0:
            self.stdout.write(self.style.WARNING('No active subscribers found.'))
            return

        self.stdout.write(f"\n{'[DRY RUN] ' if dry_run else ''}Sending to {count} subscribers...\n")

        sent = failed = 0

        for sub in subscribers:
            # Personalise the body
            name         = sub.first_name or 'Friend'
            personal_body = body.replace('{{name}}', name)
            unsubscribe_url = (
                f"{getattr(settings, 'SITE_URL', 'https://paamoja.org')}"
                f"/newsletter/unsubscribe/{sub.unsubscribe_token}/"
            )
            personal_body += (
                f"\n\n─────────────────────────────\n"
                f"To unsubscribe: {unsubscribe_url}"
            )

            if dry_run:
                self.stdout.write(f"  → Would send to: {sub.email}")
                continue

            try:
                msg = EmailMultiAlternatives(
                    subject    = subject,
                    body       = personal_body,
                    from_email = f"PaaMoja Initiative <{settings.DEFAULT_FROM_EMAIL}>",
                    to         = [sub.email],
                    reply_to   = ['info@paamoja.org'],
                )
                msg.send(fail_silently=False)
                sent += 1
                self.stdout.write(f"  ✓ {sub.email}")
            except Exception as e:
                failed += 1
                self.stdout.write(self.style.ERROR(f"  ✗ {sub.email}: {e}"))

            time.sleep(delay)

        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\n✓ Done. Sent: {sent} | Failed: {failed} | Total: {count}"
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(f"\n[DRY RUN] Would have sent to {count} subscribers.")
            )