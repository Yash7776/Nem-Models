from django.contrib import admin
from .models import Profile_header_all, User_header_all

@admin.register(Profile_header_all)
class ProfileHeaderAdmin(admin.ModelAdmin):
    list_display = ('profile_id', 'profile_name', 'is_active')

@admin.register(User_header_all)
class UserHeaderAdmin(admin.ModelAdmin):
    list_display = ('id','user_id','line_no', 'username', 'name', 'email', 'designation', 'mobile_no','profile')