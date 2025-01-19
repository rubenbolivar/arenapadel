from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from rest_framework import viewsets, generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Court, Reservation
from .serializers import CourtSerializer, ReservationSerializer

# Template Views
@login_required
def reservation_confirm_view(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)
    duration = (reservation.end_time - reservation.start_time).seconds / 3600
    total = reservation.court.price_per_hour * duration
    
    context = {
        'reservation': reservation,
        'duration': duration,
        'total': total
    }
    return render(request, 'reservations/reservation_confirm.html', context)

# API Views

# Create your views here.

class CourtViewSet(viewsets.ModelViewSet):
    queryset = Court.objects.all()
    serializer_class = CourtSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class CourtAvailabilityView(APIView):
    def get(self, request, court_id):
        try:
            court = Court.objects.get(id=court_id)
            # Add availability logic here
            return Response({'available': True})
        except Court.DoesNotExist:
            return Response({'error': 'Court not found'}, status=404)

class CourtScheduleView(APIView):
    def get(self, request, court_id):
        try:
            court = Court.objects.get(id=court_id)
            reservations = Reservation.objects.filter(
                court=court,
                start_time__gte=timezone.now()
            ).order_by('start_time')
            serializer = ReservationSerializer(reservations, many=True)
            return Response(serializer.data)
        except Court.DoesNotExist:
            return Response({'error': 'Court not found'}, status=404)

class UserReservationsView(generics.ListAPIView):
    serializer_class = ReservationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Reservation.objects.filter(user=self.request.user)
