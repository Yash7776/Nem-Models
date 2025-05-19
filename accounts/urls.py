from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('user/<str:username>/', views.user_detail, name='user_detail'),
    path('user/<str:username>/assign/<str:profile_id>/', views.assign_profile, name='assign_profile'),
    path('user/<str:username>/toggle/<int:line_no>/', views.toggle_profile_status, name='toggle_profile_status'),
]