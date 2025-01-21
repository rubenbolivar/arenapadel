from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import Payment
from .forms import PaymentForm, PaymentValidationForm

# Register your models here.

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    form = PaymentForm
    list_display = ['id', 'user', 'reservation', 'amount', 'payment_method', 'status', 'view_proof_of_payment', 'created_at']
    list_filter = ['payment_method', 'status', 'created_at']
    search_fields = ['user__username', 'user__email', 'reservation__court__name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (None, {
            'fields': ('user', 'reservation', 'amount')
        }),
        (_('Payment Details'), {
            'fields': ('payment_method', 'status', 'proof_of_payment')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def view_proof_of_payment(self, obj):
        if obj.proof_of_payment:
            return format_html('<a href="{}" target="_blank">View Proof</a>', obj.proof_of_payment.url)
        return "-"
    view_proof_of_payment.short_description = _('Proof of Payment')
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('user', 'reservation', 'amount', 'payment_method')
        return self.readonly_fields
    
    def get_form(self, request, obj=None, **kwargs):
        if obj and obj.status in ['pending', 'in_review']:
            kwargs['form'] = PaymentValidationForm
        return super().get_form(request, obj, **kwargs)
