from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'payments'

router = DefaultRouter()
router.register(r'', views.PaymentViewSet)

urlpatterns = [
    path('methods/', 
         views.PaymentMethodsView.as_view(), 
         name='payment-methods'),
    path('stripe/create-payment-intent/', 
         views.StripePaymentIntentView.as_view(), 
         name='create-payment-intent'),
    path('stripe/webhook/', 
         views.StripeWebhookView.as_view(), 
         name='stripe-webhook'),
    path('validate-payment/<int:payment_id>/', 
         views.ValidatePaymentView.as_view(), 
         name='validate-payment'),
    path('my-payments/', 
         views.UserPaymentsView.as_view(), 
         name='my-payments'),
]

urlpatterns += router.urls
