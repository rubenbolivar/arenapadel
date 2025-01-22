from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib import messages
from django.utils import timezone
from users.forms import UserRegistrationForm, UserLoginForm
from reservations.models import Court, Reservation
from datetime import datetime, timedelta

def home(request):
    latest_courts = Court.objects.filter(is_active=True)[:3]
    return render(request, 'home.html', {'latest_courts': latest_courts})

def court_list(request):
    # Get all active courts
    courts = Court.objects.filter(is_active=True)
    
    # Get filter parameters
    date_str = request.GET.get('date')
    time_str = request.GET.get('time')
    
    # Generate available hours (7:00 AM - 11:00 PM)
    available_hours = list(range(7, 23))
    
    # If date and time are provided, filter courts by availability
    if date_str and time_str:
        try:
            # Parse date and time
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            selected_hour = int(time_str)
            
            # Create datetime objects for the selected time slot
            selected_datetime = timezone.make_aware(
                datetime.combine(selected_date, datetime.min.time().replace(hour=selected_hour))
            )
            end_datetime = selected_datetime + timedelta(hours=1)
            
            # Exclude courts that have confirmed reservations during the selected time slot
            unavailable_courts = Court.objects.filter(
                reservations__status='confirmed',
                reservations__start_time__lt=end_datetime,
                reservations__end_time__gt=selected_datetime
            )
            courts = courts.exclude(id__in=unavailable_courts)
            
        except (ValueError, TypeError):
            messages.error(request, 'Por favor, selecciona una fecha y hora válidas.')
    
    context = {
        'courts': courts,
        'available_hours': available_hours,
        'today': timezone.now().date(),
    }
    return render(request, 'courts/court_list.html', context)

def court_detail(request, court_id):
    # Get the court or return 404
    court = get_object_or_404(Court, id=court_id, is_active=True)
    
    # Get filter parameters
    date_str = request.GET.get('date')
    time_str = request.GET.get('time')
    
    # Generate available hours (7:00 AM - 11:00 PM)
    available_hours = list(range(7, 23))
    
    # Generate next 7 days for the calendar display
    today = timezone.now().date()
    next_week_dates = [today + timedelta(days=i) for i in range(7)]
    
    # Initialize context
    context = {
        'court': court,
        'available_hours': available_hours,
        'today': today,
        'next_week_dates': next_week_dates,
        'selected_date': None,
        'selected_hour': None,
        'is_available': False,
    }
    
    # If date and time are provided, check specific availability
    if date_str and time_str:
        try:
            # Parse date and time
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            selected_hour = int(time_str)
            
            # Create datetime objects for the selected time slot
            selected_datetime = timezone.make_aware(
                datetime.combine(selected_date, datetime.min.time().replace(hour=selected_hour))
            )
            end_datetime = selected_datetime + timedelta(hours=1)
            
            # Check if the selected date is in the past
            if selected_date < today:
                is_available = False
                messages.error(request, 'No se pueden hacer reservas en fechas pasadas.')
            else:
                # Check if there are any confirmed reservations for this time slot
                is_available = not Reservation.objects.filter(
                    court=court,
                    status='confirmed',
                    start_time__lt=end_datetime,
                    end_time__gt=selected_datetime
                ).exists()
            
            context.update({
                'selected_date': selected_date,
                'selected_hour': selected_hour,
                'is_available': is_available,
                'selected_datetime': selected_datetime,
                'end_datetime': end_datetime,
            })
            
        except (ValueError, TypeError):
            messages.error(request, 'Por favor, selecciona una fecha y hora válidas.')
    
    # Create a dictionary to store availability for displayed dates
    availability = {}
    for date in next_week_dates:
        availability[date] = {}
        for hour in available_hours:
            # Create datetime objects for this time slot
            start_datetime = timezone.make_aware(
                datetime.combine(date, datetime.min.time().replace(hour=hour))
            )
            end_datetime = start_datetime + timedelta(hours=1)
            
            # Check if there are any confirmed reservations for this time slot
            is_slot_available = not Reservation.objects.filter(
                court=court,
                status='confirmed',
                start_time__lt=end_datetime,
                end_time__gt=start_datetime
            ).exists()
            
            availability[date][hour] = is_slot_available
    
    context['availability'] = availability
    
    return render(request, 'courts/court_detail.html', context)

@login_required
def create_reservation(request, court_id):
    if request.method == 'POST':
        court = get_object_or_404(Court, id=court_id, is_active=True)
        date_str = request.POST.get('date')
        time_str = request.POST.get('time')
        
        try:
            # Parse date and time
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            selected_hour = int(time_str)
            
            # Create datetime objects for the reservation
            start_datetime = timezone.make_aware(
                datetime.combine(selected_date, datetime.min.time().replace(hour=selected_hour))
            )
            end_datetime = start_datetime + timedelta(hours=1)
            
            # Check if the court is available
            if not Reservation.objects.filter(
                court=court,
                status='confirmed',
                start_time__lt=end_datetime,
                end_time__gt=start_datetime
            ).exists():
                # Calculate total price (1 hour at court's rate)
                total_price = court.hourly_rate
                
                # Create the reservation
                reservation = Reservation.objects.create(
                    user=request.user,
                    court=court,
                    start_time=start_datetime,
                    end_time=end_datetime,
                    total_price=total_price,
                    status='confirmed'
                )
                
                messages.success(request, '¡Reserva creada exitosamente!')
                return redirect('profile')
            else:
                messages.error(request, 'Lo sentimos, esta cancha ya no está disponible para el horario seleccionado.')
                
        except (ValueError, TypeError):
            messages.error(request, 'Por favor, selecciona una fecha y hora válidas.')
    
    return redirect('court_detail', court_id=court_id)

@login_required
def cancel_reservation(request, reservation_id):
    if request.method == 'POST':
        reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)
        
        # Check if the reservation can be cancelled (not in the past)
        if reservation.start_time.date() > timezone.now().date():
            reservation.status = 'cancelled'
            reservation.save()
            messages.success(request, 'Reserva cancelada exitosamente.')
        else:
            messages.error(request, 'No se puede cancelar una reserva pasada.')
    
    return redirect('profile')

@login_required
def profile(request):
    # Get user's reservations
    reservations = Reservation.objects.filter(
        user=request.user
    ).order_by('-start_time')  # Most recent first
    
    context = {
        'reservations': reservations
    }
    return render(request, 'users/profile.html', context)

@login_required
def profile_update(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.save()
        messages.success(request, 'Perfil actualizado exitosamente.')
        return redirect('profile')
    return redirect('profile')

def login_view(request):
    if request.method == 'POST':
        form = UserLoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, '¡Bienvenido de nuevo!')
            return redirect('home')
    else:
        form = UserLoginForm()
    return render(request, 'users/login.html', {'form': form})

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, '¡Cuenta creada exitosamente!')
            return redirect('home')
    else:
        form = UserRegistrationForm()
    return render(request, 'users/register.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, 'Has cerrado sesión correctamente.')
    return redirect('home')

def terms(request):
    return render(request, 'legal/terms.html')
