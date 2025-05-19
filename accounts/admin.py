from django.contrib import admin
from .models import Profile_header_all, User_header_all, UserProfileAssignment

@admin.register(Profile_header_all)
class ProfileHeaderAdmin(admin.ModelAdmin):
    list_display = ('profile_id', 'profile_name', 'is_active')

@admin.register(User_header_all)
class UserHeaderAdmin(admin.ModelAdmin):
    list_display = ('username', 'name', 'designation', 'mobile_no')

@admin.register(UserProfileAssignment)
class UserProfileAssignmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'profile', 'line_no', 'is_active')
    list_filter = ('is_active',)