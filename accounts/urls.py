# accounts/urls.py
from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('user/<str:username>/', views.user_detail, name='user_detail'),
    path('assign-profile/<str:username>/', views.assign_profile, name='assign_profile'),
    path('assign-profile-from-edit/<str:username>/', views.assign_profile_from_edit, name='assign_profile_from_edit'),
    path('toggle-profile/<str:username>/<int:line_no>/', views.toggle_profile_status, name='toggle_profile_status'),
    path('all-users/', views.all_users, name='all_users'),
    path('create-user/', views.create_user, name='create_user'),
    path('edit-user/<int:user_id>/', views.edit_user, name='edit_user'),
    path('toggle-user-status/<str:username>/', views.toggle_user_status, name='toggle_user_status'),
]