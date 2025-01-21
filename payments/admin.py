from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import Payment

# Register your models here.

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'reservation', 'amount', 'payment_method', 'status', 'view_proof_image', 'created_at']
    list_filter = ['payment_method', 'status', 'created_at']
    search_fields = ['user__username', 'user__email', 'reservation__court__name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('reservation', 'user', 'amount', 'payment_method', 'status')
        }),
        (_('Comprobante'), {
            'fields': ('proof_image', 'notes')
        }),
        (_('Validación'), {
            'fields': ('validated_by', 'validated_at')
        }),
        (_('Fechas'), {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def view_proof_image(self, obj):
        if obj.proof_image:
            return format_html('<a href="{}" target="_blank">View Proof</a>', obj.proof_image.url)
        return "-"
    view_proof_image.short_description = _('Proof of Payment')
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return ('reservation', 'user', 'amount', 'created_at', 'updated_at')
        return ()

    def has_add_permission(self, request):
        return False  # Los pagos solo se crean a través de la interfaz de usuario
