from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import Payment

# Register your models here.

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('reservation', 'user', 'amount', 'payment_method', 'status', 'created_at', 'view_proof_of_payment')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'reservation__court__name', 'transaction_id')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (None, {
            'fields': ('reservation', 'user', 'amount')
        }),
        (_('Payment Details'), {
            'fields': ('payment_method', 'status', 'transaction_id', 'proof_of_payment')
        }),
        (_('Additional Information'), {
            'fields': ('notes',),
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
            return ('reservation', 'user', 'amount')
        return ()
