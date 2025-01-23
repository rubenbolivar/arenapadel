from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Reservation

@receiver(post_save, sender=Reservation)
def notify_reservation_status(sender, instance, created, **kwargs):
    """Send email notifications when a reservation is created or its status changes."""
    subject = None
    message = None
    user_name = instance.user.get_full_name() or instance.user.email
    
    if created:
        subject = f'Nueva Reserva - {user_name} - {instance.court.name}'
        message = f'''Se ha creado una nueva reserva:
        
Usuario: {user_name}
Cancha: {instance.court.name}
Fecha: {instance.start_time.strftime('%d/%m/%Y')}
Hora: {instance.start_time.strftime('%H:%M')} - {instance.end_time.strftime('%H:%M')}
Estado: {instance.get_status_display()}
Monto: ${instance.total_price}'''
    
    elif instance.status == 'confirmed':
        subject = f'Reserva Confirmada - {user_name} - {instance.court.name}'
        message = f'''Tu reserva ha sido confirmada:
        
Usuario: {user_name}
Cancha: {instance.court.name}
Fecha: {instance.start_time.strftime('%d/%m/%Y')}
Hora: {instance.start_time.strftime('%H:%M')} - {instance.end_time.strftime('%H:%M')}
Estado: Confirmada
Monto: ${instance.total_price}'''
    
    elif instance.status == 'cancelled':
        subject = f'Reserva Cancelada - {user_name} - {instance.court.name}'
        message = f'''Tu reserva ha sido cancelada:
        
Usuario: {user_name}
Cancha: {instance.court.name}
Fecha: {instance.start_time.strftime('%d/%m/%Y')}
Hora: {instance.start_time.strftime('%H:%M')} - {instance.end_time.strftime('%H:%M')}'''

    if subject and message:
        # Send to admin
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [settings.DEFAULT_FROM_EMAIL],
            fail_silently=True
        )
        
        # Send to user
        if instance.user.email:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [instance.user.email],
                fail_silently=True
            )
