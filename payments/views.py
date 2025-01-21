from django.shortcuts import render
from rest_framework import viewsets, generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings
from .models import Payment
from .serializers import PaymentSerializer

# Create your views here.

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

class StripePaymentIntentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Stripe payment intent logic will go here
        return Response({'status': 'Not implemented yet'})

class StripeWebhookView(APIView):
    permission_classes = []  # No auth needed for webhooks

    def post(self, request):
        # Stripe webhook logic will go here
        return Response({'status': 'Not implemented yet'})

class ValidatePaymentView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, payment_id):
        try:
            payment = Payment.objects.get(id=payment_id)
            payment.status = 'completed'
            payment.save()
            return Response({'status': 'Payment validated'})
        except Payment.DoesNotExist:
            return Response({'error': 'Payment not found'}, status=404)

class UserPaymentsView(generics.ListAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user)


import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponse
from .models import Payment
from reservations.models import Reservation
from django.core.mail import send_mail
from django.template.loader import render_to_string

stripe.api_key = settings.STRIPE_SECRET_KEY

@login_required
def payment_method_selection(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)
    
    context = {
        'reservation': reservation,
        'stripe_public_key': settings.STRIPE_PUBLISHABLE_KEY,
        'zelle_email': settings.ZELLE_EMAIL,
        'pago_movil_phone': settings.PAGO_MOVIL_PHONE,
        'pago_movil_bank': settings.PAGO_MOVIL_BANK,
        'pago_movil_id': settings.PAGO_MOVIL_ID,
    }
    return render(request, 'payments/payment_method_selection.html', context)

@login_required
def create_stripe_checkout_session(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)
    
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'unit_amount': int(reservation.total_price * 100),  # Convert to cents
                    'product_data': {
                        'name': f'Reserva Cancha {reservation.court.name}',
                        'description': f'Fecha: {reservation.start_time.strftime("%d/%m/%Y %H:%M")}',
                    },
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=request.build_absolute_uri(
                reverse('payments:payment_success', args=[reservation_id])
            ),
            cancel_url=request.build_absolute_uri(
                reverse('payments:payment_cancel', args=[reservation_id])
            ),
            client_reference_id=str(reservation_id),
        )
        return JsonResponse({'sessionId': checkout_session.id})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def manual_payment_confirmation(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)
    
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        proof_of_payment = request.FILES.get('proof_of_payment')
        
        payment = Payment.objects.create(
            reservation=reservation,
            user=request.user,
            amount=reservation.total_price,
            payment_method=payment_method,
            status='pending',
            proof_of_payment=proof_of_payment
        )
        
        # Send email notification to admin
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
        
        messages.success(request, 'Tu confirmación de pago ha sido enviada. Te notificaremos cuando sea verificada.')
        return redirect('web:web_profile')
    
    return render(request, 'payments/manual_payment_confirmation.html', {
        'reservation': reservation
    })

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
        reservation_id = session.get('client_reference_id')
        
        if reservation_id:
            reservation = Reservation.objects.get(id=reservation_id)
            
            # Create payment record
            payment = Payment.objects.create(
                reservation=reservation,
                user=reservation.user,
                amount=reservation.total_price,
                payment_method='stripe',
                status='completed',
                transaction_id=session.get('payment_intent')
            )
            
            # Send confirmation email to user
            subject = 'Pago confirmado - ArenaPadel'
            html_message = render_to_string('payments/email/payment_success.html', {
                'payment': payment,
                'reservation': reservation,
            })
            send_mail(
                subject,
                '',
                settings.DEFAULT_FROM_EMAIL,
                [reservation.user.email],
                html_message=html_message,
                fail_silently=False,
            )

    return HttpResponse(status=200)

@login_required
def payment_success(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)
    return render(request, 'payments/payment_success.html', {'reservation': reservation})

@login_required
def payment_cancel(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)
    return render(request, 'payments/payment_cancel.html', {'reservation': reservation})

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Payment
from reservations.models import Reservation
from django.urls import reverse

@login_required
def payment_create(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)
    
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        proof_of_payment = request.FILES.get('proof_of_payment')
        
        # Validar método de pago
        if payment_method not in dict(Payment.PAYMENT_METHODS):
            messages.error(request, 'Método de pago inválido')
            return redirect('payment_create', reservation_id=reservation_id)
            
        # Para pagos en efectivo
        if payment_method == 'CASH':
            status = 'PENDING'
        # Para pagos con comprobante
        elif proof_of_payment and payment_method in ['PAGO_MOVIL', 'ZELLE']:
            status = 'REVIEWING'
        else:
            messages.error(request, 'Se requiere comprobante de pago para este método')
            return redirect('payment_create', reservation_id=reservation_id)
        
        payment = Payment.objects.create(
            reservation=reservation,
            user=request.user,
            amount=15.00,  # Por ahora precio fijo
            payment_method=payment_method,
            status=status,
            proof_of_payment=proof_of_payment if proof_of_payment else None
        )
        
        messages.success(request, 'Pago registrado correctamente')
        return redirect('payment_detail', payment_id=payment.id)
        
    return render(request, 'payments/payment_create.html', {
        'reservation': reservation,
        'payment_methods': Payment.PAYMENT_METHODS
    })

@login_required
def payment_detail(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)
    return render(request, 'payments/payment_detail.html', {'payment': payment})

# Vista para administradores
@login_required
def payment_validate(request, payment_id):
    if not request.user.is_staff:
        messages.error(request, 'No tienes permisos para validar pagos')
        return redirect('home')
        
    payment = get_object_or_404(Payment, id=payment_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve':
            payment.status = 'APPROVED'
            payment.validated_by = request.user
            payment.validated_at = timezone.now()
            payment.save()
            
            # Actualizar estado de la reserva
            payment.reservation.status = 'confirmed'
            payment.reservation.save()
            
            messages.success(request, 'Pago aprobado correctamente')
            
        elif action == 'reject':
            payment.status = 'REJECTED'
            payment.validated_by = request.user
            payment.validated_at = timezone.now()
            payment.notes = request.POST.get('rejection_reason', '')
            payment.save()
            
            messages.success(request, 'Pago rechazado')
            
    return redirect('admin:payments_payment_change', payment.id)
