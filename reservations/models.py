from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone

# Create your models here.

class Court(models.Model):
    name = models.CharField(_('name'), max_length=50)
    number = models.IntegerField(_('court number'), unique=True)
    is_active = models.BooleanField(_('active'), default=True)
    hourly_rate = models.DecimalField(_('hourly rate'), max_digits=10, decimal_places=2, default=15.00)
    
    class Meta:
        verbose_name = _('court')
        verbose_name_plural = _('courts')
        ordering = ['number']
    
    def __str__(self):
        return f"Arena {self.number}"

class Reservation(models.Model):
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('confirmed', _('Confirmed')),
        ('cancelled', _('Cancelled')),
        ('completed', _('Completed')),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reservations',
        verbose_name=_('user')
    )
    court = models.ForeignKey(
        Court,
        on_delete=models.CASCADE,
        related_name='reservations',
        verbose_name=_('court')
    )
    start_time = models.DateTimeField(_('start time'))
    end_time = models.DateTimeField(_('end time'))
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    total_price = models.DecimalField(_('total price'), max_digits=10, decimal_places=2)
    
    class Meta:
        verbose_name = _('reservation')
        verbose_name_plural = _('reservations')
        ordering = ['-start_time']
        
    def __str__(self):
        return f"{self.court} - {self.user.get_full_name()} - {self.start_time.strftime('%Y-%m-%d %H:%M')}"
    
    def clean(self):
        if self.start_time and self.end_time:
            # Check if end time is after start time
            if self.end_time <= self.start_time:
                raise ValidationError(_('End time must be after start time'))
            
            # Check if start time is in the future
            if self.start_time < timezone.now():
                raise ValidationError(_('Start time must be in the future'))
            
            # Check if reservation is within operating hours (7:00 AM - 11:00 PM)
            if self.start_time.hour < 7 or self.end_time.hour >= 23:
                raise ValidationError(_('Reservations are only available between 7:00 AM and 11:00 PM'))
            
            # Check for overlapping reservations
            overlapping = Reservation.objects.filter(
                court=self.court,
                status='confirmed',
                start_time__lt=self.end_time,
                end_time__gt=self.start_time
            ).exclude(pk=self.pk)
            
            if overlapping.exists():
                raise ValidationError(_('This court is already reserved for this time period'))
    
    def save(self, *args, **kwargs):
        if not self.total_price:
            # Calculate hours (rounded up to the nearest hour)
            duration = self.end_time - self.start_time
            hours = (duration.seconds + 3599) // 3600  # Round up
            self.total_price = self.court.hourly_rate * hours
        
        self.clean()
        super().save(*args, **kwargs)
