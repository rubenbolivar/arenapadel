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
