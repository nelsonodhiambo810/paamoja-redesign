from django.contrib import admin, messages
from django.utils.html import format_html
from django.http import HttpResponse
from django.utils import timezone
import csv

from website.email_service import send_donation_receipt
from .models import (
    Program, ProgramGallery, NewsUpdate, SuccessStory,
    TeamMember, Milestone, ContactInquiry,
    ImpactReport, VolunteerApplication,
    Donation, NewsletterSubscriber
)

# ── PROGRAM ───────────────────────────────────────────────────────────────────
class ProgramGalleryInline(admin.TabularInline):
    model  = ProgramGallery
    extra  = 3
    fields = ('image', 'caption', 'order')

@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display        = ('title', 'is_active', 'order', 'gallery_count', 'updated_at')
    list_editable       = ('is_active', 'order')
    search_fields       = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}
    list_filter         = ('is_active',)
    inlines             = [ProgramGalleryInline]
    fieldsets = (
        ('Content', {'fields': ('title', 'slug', 'description', 'full_body', 'image', 'icon')}),
        ('Impact Stats', {'fields': (('stat_1_number', 'stat_1_label'), ('stat_2_number', 'stat_2_label'), ('stat_3_number', 'stat_3_label')), 'classes': ('collapse',)}),
        ('Settings', {'fields': ('is_active', 'order')}),
    )

    def gallery_count(self, obj):
        return format_html('<span style="color:#888;">📷 {}</span>', obj.gallery.count())
    gallery_count.short_description = 'Gallery'

# ── NEWS & STORIES ────────────────────────────────────────────────────────────
@admin.register(NewsUpdate)
class NewsUpdateAdmin(admin.ModelAdmin):
    list_display        = ('title', 'date', 'is_published')
    list_editable       = ('is_published',)
    list_filter         = ('is_published', 'date')
    search_fields       = ('title', 'summary')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy      = 'date'

@admin.register(SuccessStory)
class SuccessStoryAdmin(admin.ModelAdmin):
    list_display  = ('name', 'role', 'is_featured', 'created_at')
    list_editable = ('is_featured',)
    search_fields = ('name', 'role', 'quote')

# ── ABOUT ─────────────────────────────────────────────────────────────────────
@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display  = ('name', 'role', 'is_active', 'order')
    list_editable = ('is_active', 'order')
    search_fields = ('name', 'role')

@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    list_display  = ('year', 'title', 'order')
    list_editable = ('order',)
    ordering      = ('year',)

# ── CONTACT INQUIRIES ─────────────────────────────────────────────────────────
@admin.register(ContactInquiry)
class ContactInquiryAdmin(admin.ModelAdmin):
    list_display    = ('name', 'email', 'subject_label', 'status_badge', 'created_at')
    list_filter     = ('status', 'subject', 'created_at')
    search_fields   = ('name', 'email', 'message')
    readonly_fields = ('name', 'email', 'phone', 'subject', 'message', 'created_at')
    date_hierarchy  = 'created_at'
    fieldsets = (
        ('From', {'fields': ('name', 'email', 'phone', 'subject', 'message', 'created_at')}),
        ('Admin', {'fields': ('status', 'admin_notes')}),
    )

    def subject_label(self, obj):
        return obj.get_subject_display()
    subject_label.short_description = 'Subject'

    def status_badge(self, obj):
        c = {'new': '#E88D14', 'in_progress': '#0d6efd', 'resolved': '#198754'}.get(obj.status, '#888')
        return format_html('<span style="background:{};color:white;padding:3px 10px;border-radius:20px;font-size:0.75rem;font-weight:700;">{}</span>', c, obj.get_status_display())
    status_badge.short_description = 'Status'

# ── IMPACT REPORTS ────────────────────────────────────────────────────────────
@admin.register(ImpactReport)
class ImpactReportAdmin(admin.ModelAdmin):
    list_display    = ('title', 'year', 'type_label', 'is_published', 'downloads', 'file_size_label')
    list_editable   = ('is_published',)
    list_filter     = ('report_type', 'is_published', 'year')
    search_fields   = ('title', 'description')
    readonly_fields = ('file_size_kb', 'downloads')
    ordering        = ('-year',)
    fieldsets = (
        ('Report Details', {'fields': ('title', 'report_type', 'year', 'description', 'pages')}),
        ('Files', {'fields': ('file', 'file_size_kb', 'cover_image')}),
        ('Publishing', {'fields': ('is_published', 'downloads')}),
    )

    def type_label(self, obj):
        return obj.get_report_type_display()
    type_label.short_description = 'Type'

    def file_size_label(self, obj):
        return obj.file_size_display()
    file_size_label.short_description = 'Size'

# ── VOLUNTEER APPLICATIONS ────────────────────────────────────────────────────
@admin.register(VolunteerApplication)
class VolunteerApplicationAdmin(admin.ModelAdmin):
    list_display    = ('full_name', 'email', 'phone', 'program_name', 'availability_label', 'status_badge', 'created_at')
    list_filter     = ('status', 'availability', 'commitment', 'has_experience', 'created_at', 'program')
    search_fields   = ('full_name', 'email', 'phone', 'skills', 'motivation')
    readonly_fields = ('full_name', 'email', 'phone', 'location', 'age', 'program', 'skills', 'motivation', 'availability', 'commitment', 'has_experience', 'created_at')
    date_hierarchy  = 'created_at'
    actions         = ['mark_shortlisted', 'mark_accepted', 'mark_declined']
    fieldsets = (
        ('Applicant', {'fields': ('full_name', 'email', 'phone', 'location', 'age')}),
        ('Preferences', {'fields': ('program', 'availability', 'commitment', 'has_experience')}),
        ('Application', {'fields': ('skills', 'motivation')}),
        ('Admin', {'fields': ('status', 'admin_notes', 'created_at')}),
    )

    def program_name(self, obj):
        return obj.program.title if obj.program else '—'
    program_name.short_description = 'Program'

    def availability_label(self, obj):
        return obj.get_availability_display()
    availability_label.short_description = 'Availability'

    def status_badge(self, obj):
        c = {'pending': '#E88D14', 'shortlisted': '#0d6efd', 'accepted': '#198754', 'declined': '#dc3545'}.get(obj.status, '#888')
        return format_html('<span style="background:{};color:white;padding:3px 10px;border-radius:20px;font-size:0.75rem;font-weight:700;">{}</span>', c, obj.get_status_display())
    status_badge.short_description = 'Status'

    @admin.action(description='⭐ Mark selected as Shortlisted')
    def mark_shortlisted(self, request, queryset):
        updated = queryset.update(status='shortlisted')
        self.message_user(request, f"{updated} application(s) marked as Shortlisted.", messages.SUCCESS)

    @admin.action(description='✅ Mark selected as Accepted')
    def mark_accepted(self, request, queryset):
        updated = queryset.update(status='accepted')
        self.message_user(request, f"{updated} application(s) marked as Accepted.", messages.SUCCESS)

    @admin.action(description='❌ Mark selected as Declined')
    def mark_declined(self, request, queryset):
        updated = queryset.update(status='declined')
        self.message_user(request, f"{updated} application(s) marked as Declined.", messages.WARNING)

# ── NEWSLETTER ────────────────────────────────────────────────────────────────
@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display    = ('email', 'first_name', 'source_label', 'is_active', 'subscribed_at')
    list_filter     = ('is_active', 'source', 'subscribed_at')
    search_fields   = ('email', 'first_name')
    readonly_fields = ('unsubscribe_token', 'subscribed_at', 'unsubscribed_at')
    actions         = ['export_csv', 'reactivate']

    def source_label(self, obj):
        return obj.get_source_display()
    source_label.short_description = 'Source'

    @admin.action(description='📥 Export selected subscribers to CSV')
    def export_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="paamoja_subscribers_{timezone.now().strftime("%Y%m%d")}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Email', 'First Name', 'Source', 'Active', 'Subscribed At'])
        for sub in queryset:
            writer.writerow([sub.email, sub.first_name, sub.get_source_display(), 'Yes' if sub.is_active else 'No', sub.subscribed_at.strftime('%Y-%m-%d %H:%M')])
        return response

    @admin.action(description='✅ Reactivate selected subscribers')
    def reactivate(self, request, queryset):
        updated = queryset.update(is_active=True, unsubscribed_at=None)
        self.message_user(request, f"{updated} subscriber(s) reactivated.", messages.SUCCESS)

# ── DONATIONS ─────────────────────────────────────────────────────────────────
@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display    = ('donor_display', 'phone_number', 'amount_display', 'status_badge', 'mpesa_receipt', 'receipt_badge', 'created_at')
    list_filter     = ('status', 'receipt_sent', 'created_at')
    search_fields   = ('phone_number', 'mpesa_receipt', 'checkout_request_id', 'donor_name', 'donor_email')
    readonly_fields = ('donor_name', 'donor_email', 'phone_number', 'amount', 'merchant_request_id', 'checkout_request_id', 'mpesa_receipt', 'result_description', 'receipt_sent', 'created_at', 'updated_at')
    date_hierarchy  = 'created_at'
    actions         = ['resend_receipt']
    fieldsets = (
        ('Donor', {'fields': ('donor_name', 'donor_email', 'phone_number')}),
        ('Transaction', {'fields': ('amount', 'mpesa_receipt', 'checkout_request_id', 'merchant_request_id', 'status', 'result_description')}),
        ('Receipt', {'fields': ('receipt_sent',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    def donor_display(self, obj):
        name  = obj.donor_name  or '—'
        email = obj.donor_email or ''
        if email:
            return format_html('<strong>{}</strong><br><small style="color:#888;">{}</small>', name, email)
        return format_html('<strong>{}</strong>', name)
    donor_display.short_description = 'Donor'

    def amount_display(self, obj):
        return format_html('<span style="font-weight:700;color:#5D1818;">KES {:,}</span>', int(obj.amount))
    amount_display.short_description = 'Amount'

    def status_badge(self, obj):
        c = {'success': '#198754', 'pending': '#E88D14', 'failed': '#dc3545', 'cancelled': '#6c757d'}.get(obj.status, '#888')
        return format_html('<span style="background:{};color:white;padding:3px 10px;border-radius:20px;font-size:0.75rem;font-weight:700;">{}</span>', c, obj.get_status_display())
    status_badge.short_description = 'Status'

    def receipt_badge(self, obj):
        if obj.receipt_sent:
            return format_html('<span style="background:#d4edda;color:#155724;padding:3px 10px;border-radius:20px;font-size:0.75rem;font-weight:700;">✓ Sent</span>')
        if obj.status == 'success':
            return format_html('<span style="background:#f8d7da;color:#721c24;padding:3px 10px;border-radius:20px;font-size:0.75rem;font-weight:700;">✗ Not Sent</span>')
        return format_html('<span style="color:#aaa;font-size:0.75rem;">—</span>')
    receipt_badge.short_description = 'Receipt'

    @admin.action(description='📧 Resend donation receipt email')
    def resend_receipt(self, request, queryset):
        sent = skipped = failed = 0
        for donation in queryset:
            if donation.status != 'success' or not donation.mpesa_receipt:
                skipped += 1
                continue
            if send_donation_receipt(donation):
                sent += 1
            else:
                failed += 1
        if sent: self.message_user(request, f"✓ Receipt resent for {sent} donation(s).", messages.SUCCESS)
        if skipped: self.message_user(request, f"{skipped} skipped (not successful or missing receipt).", messages.WARNING)
        if failed: self.message_user(request, f"✗ {failed} failed — check server logs.", messages.ERROR)

    def has_add_permission(self, request):
        return False