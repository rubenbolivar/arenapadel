from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'reservations'

router = DefaultRouter()
router.register(r'courts', views.CourtViewSet)
router.register(r'', views.ReservationViewSet)

urlpatterns = [
    path('courts/<int:court_id>/availability/', 
         views.CourtAvailabilityView.as_view(), 
         name='court-availability'),
    path('courts/<int:court_id>/schedule/', 
         views.CourtScheduleView.as_view(), 
         name='court-schedule'),
    path('my-reservations/', 
         views.UserReservationsView.as_view(), 
         name='my-reservations'),
]

urlpatterns += router.urls
