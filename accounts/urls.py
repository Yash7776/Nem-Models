from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.create_user, name='create_user'),
    path('user/<str:username>/', views.user_detail, name='user_detail'),
    path('user/<str:username>/assign/', views.assign_profile, name='assign_profile'),  # Removed profile_id from path
    path('user/<str:username>/toggle/<int:line_no>/', views.toggle_profile_status, name='toggle_profile_status'),
    path('all-users/', views.all_users, name='all_users'),
]