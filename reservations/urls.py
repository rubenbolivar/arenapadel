from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'reservations'

router = DefaultRouter()
router.register(r'api/courts', views.CourtViewSet, basename='api_court')
router.register(r'api/reservations', views.ReservationViewSet, basename='api_reservation')

urlpatterns = [
    # Template URLs
    path('courts/<int:court_id>/reserve/', views.court_reserve_view, name='court_reserve'),
    path('confirm/<int:reservation_id>/', views.reservation_confirm_view, name='reservation_confirm'),
    
    # API URLs
    path('api/courts/<int:court_id>/availability/', views.CourtAvailabilityView.as_view(), name='api_court_availability'),
    path('api/courts/<int:court_id>/schedule/', views.CourtScheduleView.as_view(), name='api_court_schedule'),
    path('api/my-reservations/', views.UserReservationsView.as_view(), name='api_user_reservations'),
]

urlpatterns += router.urls
