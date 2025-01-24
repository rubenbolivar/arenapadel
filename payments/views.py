from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponse
from django.core.mail import send_mail
from django.template.loader import render_to_string
from rest_framework import viewsets, generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Payment
from .serializers import PaymentSerializer
from reservations.models import Reservation
import stripe
import logging

logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Payment.objects.all()
        return Payment.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class PaymentMethodsView(APIView):
    def get(self, request):
        payment_methods = [
            {
                'id': 'stripe',
                'name': 'Credit Card (Stripe)',
                'enabled': bool(settings.STRIPE_PUBLIC_KEY),
            },
            {
                'id': 'transfer',
                'name': 'Bank Transfer',
                'enabled': True,
            },
            {
                'id': 'cash',
                'name': 'Cash',
                'enabled': True,
            }
        ]
        return Response(payment_methods)

@login_required
def payment_method_selection(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)
    
    context = {
        'reservation': reservation,
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
        'zelle_email': settings.ZELLE_EMAIL,
        'pago_movil_phone': settings.PAGO_MOVIL_PHONE,
        'pago_movil_bank': settings.PAGO_MOVIL_BANK,
        'pago_movil_id': settings.PAGO_MOVIL_ID,
    }
    return render(request, 'payments/payment_method_selection.html', context)

@login_required
def manual_payment_confirmation(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)
    payment_method = request.GET.get('method', '').upper()
    
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        proof_image = request.FILES.get('proof_image')
        reference = request.POST.get('reference')
        
        payment = Payment.objects.create(
            reservation=reservation,
            user=request.user,
            amount=reservation.total_price,
            payment_method=payment_method,
            status='REVIEWING',
            proof_image=proof_image,
            notes=f"Referencia: {reference}"
        )
        
        # Send email notification
        try:
            subject = f'Nueva confirmación de pago - Reserva #{reservation.id}'
            html_message = render_to_string('payments/email/payment_confirmation.html', {
                'payment': payment,
                'reservation': reservation,
            })
            send_mail(
                subject,
                '',
                settings.DEFAULT_FROM_EMAIL,
                [settings.ADMIN_EMAIL],
                html_message=html_message,
                fail_silently=False,
            )
            logger.info(f"Payment confirmation email sent for reservation #{reservation.id}")
        except Exception as e:
            logger.error(f"Error sending payment confirmation email: {str(e)}")
            # El pago se creó correctamente, solo falló el email
            pass
        
        messages.success(request, 'Tu confirmación de pago ha sido enviada. Te notificaremos cuando sea verificada.')
        return redirect('users:profile')
    
    context = {
        'reservation': reservation,
        'payment_method': payment_method,
        'pago_movil_bank': settings.PAGO_MOVIL_BANK,
        'pago_movil_phone': settings.PAGO_MOVIL_PHONE,
        'pago_movil_id': settings.PAGO_MOVIL_ID,
        'zelle_email': settings.ZELLE_EMAIL
    }
    return render(request, 'payments/manual_payment_confirmation.html', context)

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        # Retrieve the reservation ID from client_reference_id
        reservation_id = session.get('client_reference_id')
        if reservation_id:
            reservation = Reservation.objects.get(id=reservation_id)
            
            # Create payment record
            payment = Payment.objects.create(
                reservation=reservation,
                user=reservation.user,
                amount=session.amount_total / 100,  # Convert from cents
                payment_method='STRIPE',
                status='APPROVED',
                notes=f"Stripe Session ID: {session.id}"
            )
            
            # Update reservation status
            reservation.status = 'confirmed'
            reservation.save()
            
            # Send confirmation email
            try:
                send_payment_notification_email(payment)
            except Exception as e:
                logger.error(f"Error sending stripe payment notification: {str(e)}")

    return HttpResponse(status=200)

@login_required
def payment_success(request, reservation_id):
    messages.success(request, 'Tu pago ha sido procesado exitosamente.')
    return redirect('users:profile')

@login_required
def payment_cancel(request, reservation_id):
    messages.warning(request, 'El proceso de pago ha sido cancelado.')
    return redirect('payments:payment_method_selection', reservation_id=reservation_id)

@login_required
def payment_create(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)
    
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        proof_image = request.FILES.get('proof_image')
        
        # Validar método de pago
        if payment_method not in dict(Payment.PAYMENT_METHODS):
            messages.error(request, 'Método de pago inválido')
            return redirect('reservations:reservation_confirm', reservation_id=reservation_id)
        
        # Validar comprobante para pagos que lo requieren
        if payment_method in ['PAGO_MOVIL', 'ZELLE'] and not proof_image:
            messages.error(request, 'Se requiere comprobante de pago para este método')
            return redirect('reservations:reservation_confirm', reservation_id=reservation_id)
        
        # Crear el pago
        payment = Payment.objects.create(
            user=request.user,
            reservation=reservation,
            amount=reservation.total_price,
            payment_method=payment_method,
            proof_image=proof_image if proof_image else None,
            status='REVIEWING' if payment_method in ['PAGO_MOVIL', 'ZELLE'] else 'PENDING'
        )
        
        # Actualizar estado de la reserva
        if payment_method == 'CASH':
            reservation.status = 'pending_payment'
        else:
            reservation.status = 'confirmed' if payment_method == 'STRIPE' else 'pending_payment'
        reservation.save()
        
        # Enviar notificación por correo al admin
        try:
            send_payment_notification_email(payment)
        except Exception as e:
            logger.error(f"Error sending payment creation notification: {str(e)}")
        
        # Redirigir según el método de pago
        if payment_method == 'STRIPE':
            return redirect('payments:stripe_checkout', payment_id=payment.id)
        else:
            messages.success(request, 'Pago registrado correctamente')
            return redirect('users:profile')
    
    return redirect('reservations:reservation_confirm', reservation_id=reservation_id)

@login_required
def payment_detail(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    return render(request, 'payments/payment_detail.html', {'payment': payment})

@login_required
def payment_validate(request, payment_id):
    if not request.user.is_staff:
        messages.error(request, 'No tienes permisos para realizar esta acción')
        return redirect('home')
        
    payment = get_object_or_404(Payment, id=payment_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve':
            payment.status = 'APPROVED'
            payment.validated_by = request.user
            payment.validated_at = timezone.now()
            payment.save()
            
            # Update reservation status
            payment.reservation.status = 'confirmed'
            payment.reservation.save()
            
            messages.success(request, 'Pago aprobado correctamente')
            
        elif action == 'reject':
            payment.status = 'REJECTED'
            payment.validated_by = request.user
            payment.validated_at = timezone.now()
            payment.save()
            
            messages.warning(request, 'Pago rechazado')
            
    return redirect('payments:payment_detail', payment_id=payment_id)

def send_payment_notification_email(payment):
    subject = f'Nuevo pago registrado - Reserva #{payment.reservation.id}'
    html_message = render_to_string('payments/email/payment_notification.html', {
        'payment': payment,
        'reservation': payment.reservation,
    })
    send_mail(
        subject,
        '',
        settings.DEFAULT_FROM_EMAIL,
        [settings.ADMIN_EMAIL],
        html_message=html_message,
        fail_silently=False,
    )
