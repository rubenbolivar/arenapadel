from django.urls import path
from . import views

urlpatterns = [
    path('reservation/<int:reservation_id>/payment/', 
         views.payment_method_selection, 
         name='payment_select'),
    
    path('reservation/<int:reservation_id>/create/',
         views.create_stripe_checkout_session,
         name='payment_create'),
    
    path('reservation/<int:reservation_id>/confirm/',
         views.manual_payment_confirmation,
         name='payment_confirm'),
    
    path('webhook/stripe/',
         views.stripe_webhook,
         name='payment_webhook'),
    
    path('reservation/<int:reservation_id>/success/',
         views.payment_success,
         name='payment_success'),
    
    path('reservation/<int:reservation_id>/cancel/',
         views.payment_cancel,
         name='payment_cancel'),
]
