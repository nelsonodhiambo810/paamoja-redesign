from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from django.utils.crypto import get_random_string

# ── PROGRAMS ──────────────────────────────────────────────────────────────────
class Program(models.Model):
    title       = models.CharField(max_length=100)
    slug        = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    full_body   = models.TextField(blank=True, help_text="Full program description")
    image       = models.ImageField(upload_to='programs/', blank=True, null=True)
    icon        = models.CharField(max_length=60, blank=True, help_text="Font Awesome class")
    stat_1_number = models.CharField(max_length=20, blank=True)
    stat_1_label  = models.CharField(max_length=60, blank=True)
    stat_2_number = models.CharField(max_length=20, blank=True)
    stat_2_label  = models.CharField(max_length=60, blank=True)
    stat_3_number = models.CharField(max_length=20, blank=True)
    stat_3_label  = models.CharField(max_length=60, blank=True)
    is_active  = models.BooleanField(default=True)
    order      = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'title']
        verbose_name = 'Program'
        verbose_name_plural = 'Programs'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('website:program_detail', kwargs={'slug': self.slug})

    def __str__(self):
        return self.title

class ProgramGallery(models.Model):
    program   = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='gallery')
    image     = models.ImageField(upload_to='programs/gallery/')
    caption   = models.CharField(max_length=200, blank=True)
    order     = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = 'Gallery Image'
        verbose_name_plural = 'Gallery Images'

# ── NEWS & STORIES ────────────────────────────────────────────────────────────
class NewsUpdate(models.Model):
    title        = models.CharField(max_length=200)
    slug         = models.SlugField(unique=True, blank=True)
    date         = models.DateField()
    link         = models.URLField(blank=True)
    summary      = models.TextField(blank=True)
    is_published = models.BooleanField(default=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']
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
        ordering = ['-created_at']
        verbose_name = 'Success Story'
        verbose_name_plural = 'Success Stories'

    def __str__(self):
        return self.name

# ── ABOUT ─────────────────────────────────────────────────────────────────────
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
        ordering = ['order', 'name']
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
        ordering = ['year', 'order']
        verbose_name = 'Milestone'
        verbose_name_plural = 'Milestones'

    def __str__(self):
        return f"{self.year}: {self.title}"

# ── CONTACT ───────────────────────────────────────────────────────────────────
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
        ordering = ['-created_at']
        verbose_name = 'Contact Inquiry'
        verbose_name_plural = 'Contact Inquiries'

    def __str__(self):
        return f"[{self.get_status_display()}] {self.name} — {self.get_subject_display()}"

# ── IMPACT REPORTS ────────────────────────────────────────────────────────────
class ImpactReport(models.Model):
    REPORT_TYPE_CHOICES = [
        ('annual',    'Annual Report'),
        ('program',   'Program Report'),
        ('financial', 'Financial Statement'),
        ('research',  'Research / Study'),
        ('other',     'Other'),
    ]

    title         = models.CharField(max_length=200)
    report_type   = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES, default='annual')
    year          = models.PositiveIntegerField(help_text="Year this report covers e.g. 2024")
    description   = models.TextField(blank=True, help_text="Short summary shown on the reports listing page")
    cover_image   = models.ImageField(upload_to='reports/covers/', blank=True, null=True, help_text="Optional cover thumbnail")
    file          = models.FileField(upload_to='reports/files/', help_text="Upload the PDF report")
    file_size_kb  = models.PositiveIntegerField(default=0, editable=False, help_text="Auto-calculated on save")
    pages         = models.PositiveIntegerField(default=0, blank=True, help_text="Number of pages (optional)")
    is_published  = models.BooleanField(default=True)
    downloads     = models.PositiveIntegerField(default=0, editable=False, help_text="Auto-incremented on each download")
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-year', '-created_at']
        verbose_name = 'Impact Report'
        verbose_name_plural = 'Impact Reports'

    def save(self, *args, **kwargs):
        if self.file:
            try:
                self.file_size_kb = round(self.file.size / 1024)
            except Exception:
                pass
        super().save(*args, **kwargs)

    def file_size_display(self):
        if self.file_size_kb >= 1024:
            return f"{self.file_size_kb / 1024:.1f} MB"
        return f"{self.file_size_kb} KB"

    def __str__(self):
        return f"{self.year} — {self.title}"

# ── VOLUNTEERS ────────────────────────────────────────────────────────────────
class VolunteerApplication(models.Model):
    AVAILABILITY_CHOICES = [
        ('weekdays',  'Weekdays (Mon–Fri)'),
        ('weekends',  'Weekends (Sat–Sun)'),
        ('evenings',  'Evenings only'),
        ('flexible',  'Flexible / Remote'),
    ]
    COMMITMENT_CHOICES = [
        ('once_off',  'Once-off event'),
        ('weekly',    'Weekly'),
        ('monthly',   'Monthly'),
        ('long_term', 'Long-term (6+ months)'),
    ]
    STATUS_CHOICES = [
        ('pending',   'Pending Review'),
        ('shortlisted','Shortlisted'),
        ('accepted',  'Accepted'),
        ('declined',  'Declined'),
    ]

    full_name   = models.CharField(max_length=100)
    email       = models.EmailField()
    phone       = models.CharField(max_length=20)
    location    = models.CharField(max_length=100, blank=True)
    age         = models.PositiveIntegerField(blank=True, null=True)
    program     = models.ForeignKey(Program, on_delete=models.SET_NULL, null=True, blank=True, related_name='volunteers')
    skills      = models.TextField()
    motivation  = models.TextField()
    availability   = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, default='weekends')
    commitment     = models.CharField(max_length=20, choices=COMMITMENT_CHOICES, default='monthly')
    has_experience = models.BooleanField(default=False)
    status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Volunteer Application'
        verbose_name_plural = 'Volunteer Applications'

    def __str__(self):
        return f"[{self.get_status_display()}] {self.full_name} — {self.email}"

# ── NEWSLETTER ────────────────────────────────────────────────────────────────
class NewsletterSubscriber(models.Model):
    SOURCE_CHOICES = [
        ('homepage',  'Homepage Footer'),
        ('popup',     'Exit-Intent Popup'),
        ('contact',   'Contact Page'),
        ('volunteer', 'Volunteer Page'),
        ('manual',    'Manually Added'),
    ]

    email             = models.EmailField(unique=True)
    first_name        = models.CharField(max_length=60, blank=True)
    source            = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='homepage')
    is_active         = models.BooleanField(default=True)
    unsubscribe_token = models.CharField(max_length=64, unique=True, blank=True)
    subscribed_at     = models.DateTimeField(auto_now_add=True)
    unsubscribed_at   = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-subscribed_at']
        verbose_name = 'Newsletter Subscriber'
        verbose_name_plural = 'Newsletter Subscribers'

    def save(self, *args, **kwargs):
        if not self.unsubscribe_token:
            self.unsubscribe_token = get_random_string(64)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email

# ── DONATIONS ─────────────────────────────────────────────────────────────────
class Donation(models.Model):
    STATUS_CHOICES = [
        ('pending',   'Pending'),
        ('success',   'Success'),
        ('failed',    'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    donor_name          = models.CharField(max_length=100, blank=True)
    donor_email         = models.EmailField(blank=True)
    phone_number        = models.CharField(max_length=20)
    amount              = models.DecimalField(max_digits=10, decimal_places=2)
    merchant_request_id = models.CharField(max_length=100, blank=True)
    checkout_request_id = models.CharField(max_length=100, blank=True, db_index=True)
    mpesa_receipt       = models.CharField(max_length=50, blank=True)
    status              = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    result_description  = models.TextField(blank=True)
    receipt_sent        = models.BooleanField(default=False)
    created_at          = models.DateTimeField(auto_now_add=True)
    updated_at          = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Donation'
        verbose_name_plural = 'Donations'

    def __str__(self):
        return f"{self.phone_number} — KES {self.amount} [{self.status}]"