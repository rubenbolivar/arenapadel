from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('reservation/<int:reservation_id>/payment/', 
         views.payment_method_selection, 
         name='payment_method_selection'),
    
    path('reservation/<int:reservation_id>/create-checkout-session/',
         views.create_stripe_checkout_session,
         name='create_checkout_session'),
    
    path('reservation/<int:reservation_id>/manual-confirmation/',
         views.manual_payment_confirmation,
         name='manual_payment_confirmation'),
    
    path('webhook/stripe/',
         views.stripe_webhook,
         name='stripe_webhook'),
    
    path('reservation/<int:reservation_id>/success/',
         views.payment_success,
         name='payment_success'),
    
    path('reservation/<int:reservation_id>/cancel/',
         views.payment_cancel,
         name='payment_cancel'),
]
