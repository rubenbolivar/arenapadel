from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages
from rest_framework import viewsets, generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Court, Reservation
from .serializers import CourtSerializer, ReservationSerializer

# Template Views
@login_required
def court_reserve_view(request, court_id):
    court = get_object_or_404(Court, id=court_id)
    
    if request.method == 'POST':
        date = request.POST.get('date')
        time = request.POST.get('time')
        duration = float(request.POST.get('duration', 1))
        
        if date and time:
            try:
                # Combine date and time
                start_time = timezone.datetime.strptime(f"{date} {time}", '%Y-%m-%d %H:%M')
                end_time = start_time + timezone.timedelta(hours=duration)
                
                # Create reservation
                reservation = Reservation.objects.create(
                    user=request.user,
                    court=court,
                    start_time=start_time,
                    end_time=end_time,
                    status='pending'
                )
                
                return redirect('reservations:reservation_confirm', reservation_id=reservation.id)
            except ValueError:
                messages.error(request, 'Fecha u hora inválida')
                return redirect('court_detail', court_id=court_id)
    
    context = {
        'court': court,
        'min_date': timezone.now().date(),
        'max_date': (timezone.now() + timezone.timedelta(days=30)).date(),
    }
    return render(request, 'reservations/court_reserve.html', context)

@login_required
def reservation_confirm_view(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)
    duration = (reservation.end_time - reservation.start_time).seconds / 3600
    total = reservation.court.hourly_rate * duration
    
    context = {
        'reservation': reservation,
        'duration': duration,
        'total': total
    }
    return render(request, 'reservations/reservation_confirm.html', context)

# API Views
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
        court = get_object_or_404(Court, id=court_id)
        date = request.query_params.get('date')
        
        if not date:
            return Response({'error': 'Date parameter is required'}, status=400)
        
        try:
            date = timezone.datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': 'Invalid date format'}, status=400)
        
        # Get all reservations for this court on this date
        reservations = Reservation.objects.filter(
            court=court,
            start_time__date=date,
            status__in=['confirmed', 'pending']
        )
        
        # Create a list of all hours in a day
        hours = list(range(7, 23))  # 7 AM to 10 PM
        
        # Mark hours as unavailable if there's a reservation
        available_hours = []
        for hour in hours:
            hour_start = timezone.datetime.combine(date, timezone.datetime.min.time().replace(hour=hour))
            hour_end = hour_start + timezone.timedelta(hours=1)
            
            is_available = not reservations.filter(
                start_time__lt=hour_end,
                end_time__gt=hour_start
            ).exists()
            
            if is_available:
                available_hours.append(hour)
        
        return Response({
            'date': date,
            'available_hours': available_hours
        })

class CourtScheduleView(APIView):
    def get(self, request, court_id):
        court = get_object_or_404(Court, id=court_id)
        start_date = timezone.now().date()
        end_date = start_date + timezone.timedelta(days=7)
        
        # Get all reservations for this period
        reservations = Reservation.objects.filter(
            court=court,
            start_time__date__range=[start_date, end_date],
            status__in=['confirmed', 'pending']
        )
        
        # Create schedule data
        schedule = []
        current_date = start_date
        while current_date <= end_date:
            day_reservations = reservations.filter(start_time__date=current_date)
            schedule.append({
                'date': current_date,
                'reservations': ReservationSerializer(day_reservations, many=True).data
            })
            current_date += timezone.timedelta(days=1)
        
        return Response(schedule)

class UserReservationsView(generics.ListAPIView):
    serializer_class = ReservationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Reservation.objects.filter(user=self.request.user)
