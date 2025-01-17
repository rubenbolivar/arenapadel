from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Court, Reservation

# Register your models here.

@admin.register(Court)
class CourtAdmin(admin.ModelAdmin):
    list_display = ('name', 'number', 'hourly_rate', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'number')
    ordering = ('number',)

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('court', 'user', 'start_time', 'end_time', 'status', 'total_price')
    list_filter = ('status', 'court', 'start_time')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'court__name')
    ordering = ('-start_time',)
    date_hierarchy = 'start_time'
    
    fieldsets = (
        (None, {
            'fields': ('court', 'user')
        }),
        (_('Reservation Details'), {
            'fields': ('start_time', 'end_time', 'status', 'total_price')
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return ('total_price',)
        return ()
