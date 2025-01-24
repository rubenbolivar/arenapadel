from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import Payment
from .forms import PaymentForm, PaymentValidationForm

# Register your models here.

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    form = PaymentForm
    list_display = ['id', 'user', 'reservation', 'amount', 'payment_method', 'status', 'view_proof_image', 'created_at']
    list_filter = ['payment_method', 'status', 'created_at']
    search_fields = ['user__username', 'user__email', 'reservation__court__name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    actions = ['approve_payments', 'reject_payments']
    
    fieldsets = (
        (None, {
            'fields': ('user', 'reservation', 'amount')
        }),
        (_('Payment Details'), {
            'fields': ('payment_method', 'status', 'proof_image')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def approve_payments(self, request, queryset):
        for payment in queryset:
            payment.status = 'APPROVED'
            payment.save()
            
            # Actualizar el estado de la reserva
            if payment.reservation:
                payment.reservation.status = 'confirmed'
                payment.reservation.save()
    approve_payments.short_description = _("Aprobar pagos seleccionados")

    def reject_payments(self, request, queryset):
        for payment in queryset:
            payment.status = 'REJECTED'
            payment.save()
    reject_payments.short_description = _("Rechazar pagos seleccionados")

    def view_proof_image(self, obj):
        if obj.proof_image:
            return format_html('<a href="{}" target="_blank">View Proof</a>', obj.proof_image.url)
        return "-"
    view_proof_image.short_description = _('Proof of Payment')
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('user', 'reservation', 'amount', 'payment_method')
        return self.readonly_fields
    
    def get_form(self, request, obj=None, **kwargs):
        if obj and obj.status in ['pending', 'in_review']:
            kwargs['form'] = PaymentValidationForm
        return super().get_form(request, obj, **kwargs)
