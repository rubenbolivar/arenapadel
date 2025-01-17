from django.shortcuts import render
from rest_framework import viewsets, generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from .models import Court, Reservation
from .serializers import CourtSerializer, ReservationSerializer

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
