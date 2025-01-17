from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from reservations.models import Reservation

class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('pago_movil', _('Pago Móvil')),
        ('zelle', 'Zelle'),
        ('bank_transfer', _('Bank Transfer')),
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
        ('cash', _('Cash')),
    ]
    
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('processing', _('Processing')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
        ('refunded', _('Refunded')),
    ]
    
    reservation = models.ForeignKey(
        Reservation,
        on_delete=models.CASCADE,
        related_name='payments',
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
        choices=PAYMENT_METHOD_CHOICES
    )
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    transaction_id = models.CharField(
        _('transaction ID'),
        max_length=255,
        blank=True,
        null=True
    )
    proof_of_payment = models.ImageField(
        _('proof of payment'),
        upload_to='payment_proofs/',
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    notes = models.TextField(_('notes'), blank=True)
    
    class Meta:
        verbose_name = _('payment')
        verbose_name_plural = _('payments')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_payment_method_display()} - {self.amount} USD - {self.reservation}"
    
    def save(self, *args, **kwargs):
        # If payment is completed, update reservation status
        if self.status == 'completed' and self.reservation.status == 'pending':
            self.reservation.status = 'confirmed'
            self.reservation.save()
        super().save(*args, **kwargs)
