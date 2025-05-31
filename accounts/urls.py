from django.urls import path
from . import views

urlpatterns = [
    path('user/<str:username>/', views.user_detail, name='user_detail'),
    path('assign-profile/<str:username>/', views.assign_profile, name='assign_profile'),
    path('assign-profile-from-edit/<str:username>/', views.assign_profile_from_edit, name='assign_profile_from_edit'),
    path('toggle-profile-status/<str:username>/<int:line_no>/', views.toggle_profile_status, name='toggle_profile_status'),
    path('all-users/', views.all_users, name='all_users'),
    path('create-user/', views.create_user, name='create_user'),
    path('edit-user/<int:user_id>/', views.edit_user, name='edit_user'),
    path('toggle-user-status/<str:username>/', views.toggle_user_status, name='toggle_user_status'),
    path('users-summary/', views.users_summary, name='users_summary'),
    path('get-districts/<int:state_id>/', views.get_districts, name='get_districts'),
    path('get-talukas/<int:district_id>/', views.get_talukas, name='get_talukas'),
    path('get-villages/<int:taluka_id>/', views.get_villages, name='get_villages'),
    path('manage-locations/', views.manage_locations, name='manage_locations'),
    path('save-project-location/', views.save_project_location, name='save_project_location'),
    path('project-combination/', views.project_combination, name='project_combination'),
    path('save-project-combination/', views.save_project_combination, name='save_project_combination'),
    path('search-states/', views.search_states, name='search_states'),
    path('search-districts/', views.search_districts, name='search_districts'),
    path('search-talukas/', views.search_talukas, name='search_talukas'),
    path('search-villages/', views.search_villages, name='search_villages'),
    path('add-district/', views.add_district, name='add_district'),
    path('add-taluka/', views.add_taluka, name='add_taluka'),
    path('add-village/', views.add_village, name='add_village'),
    path('get-projects/<str:dept_id>/', views.get_projects_by_department, name='get_projects_by_department'),
]