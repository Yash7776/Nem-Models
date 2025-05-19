from django.contrib import admin
from .models import Profile_header_all, User_header_all, UniqueIdHeaderAll

@admin.register(Profile_header_all)
class ProfileHeaderAdmin(admin.ModelAdmin):
    list_display = ('profile_id', 'profile_name', 'is_active')

@admin.register(User_header_all)
class UserHeaderAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'username', 'name', 'email', 'designation', 'mobile_no', 'line_no', 'profile', 'is_active','created_on','updated_on')

@admin.register(UniqueIdHeaderAll)
class UniqueIdHeaderAllAdmin(admin.ModelAdmin):
    list_display = ('table_name', 'id_for', 'prefix', 'last_id', 'created_on', 'modified_on')