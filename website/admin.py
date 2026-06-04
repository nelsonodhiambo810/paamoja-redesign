from django.contrib import admin, messages
from django.utils.html import format_html
from website.email_service import send_donation_receipt
from .models import (
    Program, NewsUpdate, SuccessStory, Donation,
    TeamMember, Milestone, ContactInquiry,
)

@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display  = ('title', 'is_active', 'order', 'updated_at')
    list_editable = ('is_active', 'order')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}
    list_filter   = ('is_active',)

@admin.register(NewsUpdate)
class NewsUpdateAdmin(admin.ModelAdmin):
    list_display  = ('title', 'date', 'is_published')
    list_editable = ('is_published',)
    list_filter   = ('is_published', 'date')
    search_fields = ('title', 'summary')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'date'

@admin.register(SuccessStory)
class SuccessStoryAdmin(admin.ModelAdmin):
    list_display  = ('name', 'role', 'is_featured', 'created_at')
    list_editable = ('is_featured',)
    search_fields = ('name', 'role', 'quote')

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

@admin.register(ContactInquiry)
class ContactInquiryAdmin(admin.ModelAdmin):
    list_display  = ('name', 'email', 'subject_display', 'status_badge', 'created_at')
    list_filter   = ('status', 'subject', 'created_at')
    search_fields = ('name', 'email', 'message')
    readonly_fields = ('name', 'email', 'phone', 'subject', 'message', 'created_at')
    list_editable  = ()
    date_hierarchy = 'created_at'
    fieldsets = (
        ('Sender Details', {
            'fields': ('name', 'email', 'phone', 'subject', 'message', 'created_at')
        }),
        ('Admin', {
            'fields': ('status', 'admin_notes')
        }),
    )

    def subject_display(self, obj):
        return obj.get_subject_display()
    subject_display.short_description = 'Subject'

    def status_badge(self, obj):
        colours = {'new': '#E88D14', 'in_progress': '#0d6efd', 'resolved': 'green'}
        c = colours.get(obj.status, 'grey')
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:8px;font-size:0.75rem;">{}</span>',
            c, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = (
        'donor_display', 'phone_number', 'amount_display',
        'status_badge', 'mpesa_receipt', 'receipt_badge', 'created_at',
    )
    list_filter     = ('status', 'receipt_sent', 'created_at')
    search_fields   = ('phone_number', 'mpesa_receipt', 'checkout_request_id',
                       'donor_name', 'donor_email')
    readonly_fields = (
        'donor_name', 'donor_email', 'phone_number', 'amount',
        'merchant_request_id', 'checkout_request_id', 'mpesa_receipt',
        'result_description', 'receipt_sent', 'created_at', 'updated_at',
    )
    date_hierarchy = 'created_at'
    actions        = ['resend_receipt']

    fieldsets = (
        ('Donor', {
            'fields': ('donor_name', 'donor_email', 'phone_number')
        }),
        ('Transaction', {
            'fields': ('amount', 'mpesa_receipt', 'checkout_request_id',
                       'merchant_request_id', 'status', 'result_description')
        }),
        ('Receipt', {
            'fields': ('receipt_sent',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def donor_display(self, obj):
        name  = obj.donor_name  or '—'
        email = obj.donor_email or ''
        if email:
            return format_html(
                '<strong>{}</strong><br><small style="color:#888;">{}</small>',
                name, email
            )
        return format_html('<strong>{}</strong>', name)
    donor_display.short_description = 'Donor'

    def amount_display(self, obj):
        return format_html(
            '<span style="font-weight:700; color:#5D1818;">KES {:,}</span>',
            int(obj.amount)
        )
    amount_display.short_description = 'Amount'

    def status_badge(self, obj):
        colours = {
            'success':   '#198754',
            'pending':   '#E88D14',
            'failed':    '#dc3545',
            'cancelled': '#6c757d',
        }
        c = colours.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background:{};color:white;padding:3px 10px;'
            'border-radius:20px;font-size:0.75rem;font-weight:700;">{}</span>',
            c, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def receipt_badge(self, obj):
        if obj.receipt_sent:
            return format_html(
                '<span style="background:#d4edda;color:#155724;padding:3px 10px;'
                'border-radius:20px;font-size:0.75rem;font-weight:700;">✓ Sent</span>'
            )
        if obj.status == 'success':
            return format_html(
                '<span style="background:#f8d7da;color:#721c24;padding:3px 10px;'
                'border-radius:20px;font-size:0.75rem;font-weight:700;">✗ Not Sent</span>'
            )
        return format_html('<span style="color:#aaa;font-size:0.75rem;">—</span>')
    receipt_badge.short_description = 'Receipt'

    @admin.action(description='📧 Resend donation receipt email')
    def resend_receipt(self, request, queryset):
        sent, skipped, failed = 0, 0, 0
        for donation in queryset:
            if donation.status != 'success' or not donation.mpesa_receipt:
                skipped += 1
                continue
            if send_donation_receipt(donation):
                sent += 1
            else:
                failed += 1
        if sent: self.message_user(request, f"✓ {sent} receipt(s) resent.", messages.SUCCESS)
        if skipped: self.message_user(request, f"{skipped} skipped.", messages.WARNING)
        if failed: self.message_user(request, f"✗ {failed} failed.", messages.ERROR)

    def has_add_permission(self, request):
        return False