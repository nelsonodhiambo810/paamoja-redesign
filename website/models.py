"""
PaaMoja Website Models — Sprint 1 Complete
All models consolidated in one file.
"""

from django.db import models
from django.utils.text import slugify


# ── CONTENT MODELS ────────────────────────────────────────────────────────────

class Program(models.Model):
    title       = models.CharField(max_length=100)
    slug        = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    image       = models.ImageField(upload_to='programs/', blank=True, null=True)
    is_active   = models.BooleanField(default=True)
    order       = models.PositiveIntegerField(default=0)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering     = ['order', 'title']
        verbose_name = 'Program'
        verbose_name_plural = 'Programs'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class NewsUpdate(models.Model):
    title        = models.CharField(max_length=200)
    slug         = models.SlugField(unique=True, blank=True)
    date         = models.DateField()
    link         = models.URLField(blank=True)
    summary      = models.TextField(blank=True)
    is_published = models.BooleanField(default=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering     = ['-date']
        verbose_name = 'News Update'
        verbose_name_plural = 'News Updates'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class SuccessStory(models.Model):
    name        = models.CharField(max_length=100)
    role        = models.CharField(max_length=100)
    quote       = models.TextField()
    photo       = models.ImageField(upload_to='stories/', blank=True, null=True)
    is_featured = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering     = ['-created_at']
        verbose_name = 'Success Story'
        verbose_name_plural = 'Success Stories'

    def __str__(self):
        return self.name


# ── ABOUT PAGE MODELS ─────────────────────────────────────────────────────────

class TeamMember(models.Model):
    name         = models.CharField(max_length=100)
    role         = models.CharField(max_length=100)
    bio          = models.TextField(blank=True)
    photo        = models.ImageField(upload_to='team/', blank=True, null=True)
    email        = models.EmailField(blank=True)
    linkedin_url = models.URLField(blank=True)
    order        = models.PositiveIntegerField(default=0)
    is_active    = models.BooleanField(default=True)

    class Meta:
        ordering     = ['order', 'name']
        verbose_name = 'Team Member'
        verbose_name_plural = 'Team Members'

    def __str__(self):
        return f"{self.name} — {self.role}"


class Milestone(models.Model):
    year        = models.PositiveIntegerField()
    title       = models.CharField(max_length=200)
    description = models.TextField()
    order       = models.PositiveIntegerField(default=0)

    class Meta:
        ordering     = ['year', 'order']
        verbose_name = 'Milestone'
        verbose_name_plural = 'Milestones'

    def __str__(self):
        return f"{self.year}: {self.title}"


# ── CONTACT MODEL ─────────────────────────────────────────────────────────────

class ContactInquiry(models.Model):
    SUBJECT_CHOICES = [
        ('partnership', 'Partnership Opportunity'),
        ('volunteer',   'Volunteering'),
        ('donation',    'Donation / Funding'),
        ('media',       'Media / Press'),
        ('general',     'General Inquiry'),
    ]
    STATUS_CHOICES = [
        ('new',         'New'),
        ('in_progress', 'In Progress'),
        ('resolved',    'Resolved'),
    ]

    name        = models.CharField(max_length=100)
    email       = models.EmailField()
    phone       = models.CharField(max_length=20, blank=True)
    subject     = models.CharField(max_length=30, choices=SUBJECT_CHOICES, default='general')
    message     = models.TextField()
    status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    admin_notes = models.TextField(blank=True, help_text="Internal notes — not visible to sender")
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering     = ['-created_at']
        verbose_name = 'Contact Inquiry'
        verbose_name_plural = 'Contact Inquiries'

    def __str__(self):
        return f"[{self.get_status_display()}] {self.name} — {self.get_subject_display()}"


# ── DONATIONS ─────────────────────────────────────────────────────────────────

"""
Donation model update for Sprint 2.
Replace the Donation class in your existing website/models.py with this version.
The two new fields (donor_name, donor_email) allow the receipt to be personalised
and sent to the right inbox.
"""


class Donation(models.Model):
    STATUS_CHOICES = [
        ('pending',   'Pending'),
        ('success',   'Success'),
        ('failed',    'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    # ── Donor identity (collected in modal before STK Push) ───────────────────
    donor_name          = models.CharField(max_length=100, blank=True,
                                           help_text="Collected from modal form")
    donor_email         = models.EmailField(blank=True,
                                            help_text="Where the receipt email is sent")

    # ── Transaction data ──────────────────────────────────────────────────────
    phone_number        = models.CharField(max_length=20)
    amount              = models.DecimalField(max_digits=10, decimal_places=2)
    merchant_request_id = models.CharField(max_length=100, blank=True)
    checkout_request_id = models.CharField(max_length=100, blank=True, db_index=True)
    mpesa_receipt       = models.CharField(max_length=50, blank=True)
    status              = models.CharField(max_length=20, choices=STATUS_CHOICES,
                                           default='pending')
    result_description  = models.TextField(blank=True)
    receipt_sent        = models.BooleanField(default=False,
                                              help_text="True once receipt email was dispatched")

    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering     = ['-created_at']
        verbose_name = 'Donation'
        verbose_name_plural = 'Donations'

    def __str__(self):
        return f"{self.phone_number} — KES {self.amount} [{self.status}]"