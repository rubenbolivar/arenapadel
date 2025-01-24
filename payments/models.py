from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from reservations.models import Reservation

class Payment(models.Model):
    PAYMENT_METHODS = [
        ('PAGO_MOVIL', _('Pago Móvil')),
        ('ZELLE', _('Zelle')),
        ('CASH', _('Efectivo')),
        ('STRIPE', _('Stripe')),
        ('PAYPAL', _('PayPal')),
    ]

    PAYMENT_STATUS = [
        ('PENDING', _('Pendiente')),
        ('REVIEWING', _('En Revisión')),
        ('APPROVED', _('Aprobado')),
        ('REJECTED', _('Rechazado')),
        ('CANCELLED', _('Cancelado')),
    ]
    
    reservation = models.OneToOneField(
        Reservation,
        on_delete=models.CASCADE,
        related_name='payment_set',
        verbose_name=_('reservation')
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name=_('user')
    )
    amount = models.DecimalField(_('amount'), max_digits=10, decimal_places=2)
    payment_method = models.CharField(
        _('payment method'),
        max_length=20,
        choices=PAYMENT_METHODS
    )
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=PAYMENT_STATUS,
        default='PENDING'
    )
    proof_image = models.ImageField(
        _('proof of payment'),
        upload_to='payment_proofs/',
        null=True,
        blank=True
    )
    notes = models.TextField(_('notes'), blank=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    validated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='validated_payments'
    )
    validated_at = models.DateTimeField(_('validated at'), null=True, blank=True)

    class Meta:
        verbose_name = _('payment')
        verbose_name_plural = _('payments')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Payment {self.id} - {self.get_payment_method_display()} - {self.get_status_display()}"
