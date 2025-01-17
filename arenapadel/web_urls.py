from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'web'

urlpatterns = [
    path('', views.home, name='web_home'),
    path('courts/', views.court_list, name='web_court_list'),
    path('courts/<int:court_id>/', views.court_detail, name='web_court_detail'),
    path('courts/<int:court_id>/reserve/', views.create_reservation, name='web_create_reservation'),
    path('reservations/<int:reservation_id>/cancel/', views.cancel_reservation, name='web_cancel_reservation'),
    path('profile/', views.profile, name='web_profile'),
    path('profile/update/', views.profile_update, name='web_profile_update'),
    path('login/', views.login_view, name='web_login'),
    path('register/', views.register, name='web_register'),
    path('logout/', views.logout_view, name='web_logout'),
    path('terms/', views.terms, name='web_terms'),
    
    # Password Reset URLs
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='users/password_reset.html',
             email_template_name='users/password_reset_email.html',
             subject_template_name='users/password_reset_subject.txt'
         ),
         name='web_password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='users/password_reset_done.html'
         ),
         name='web_password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='users/password_reset_confirm.html'
         ),
         name='web_password_reset_confirm'),
    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='users/password_reset_complete.html'
         ),
         name='web_password_reset_complete'),
]
