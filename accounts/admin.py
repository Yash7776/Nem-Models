from django.contrib import admin
from .models import Profile_header_all, User_header_all, UniqueIdHeaderAll

@admin.register(Profile_header_all)
class ProfileHeaderAdmin(admin.ModelAdmin):
    list_display = ('profile_id', 'profile_name', 'p_status', 'p_inserted_on', 'p_deactivated_on')
    ordering = ('profile_id',)  # ascending order by profile_id

@admin.register(User_header_all)
class UserHeaderAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user_id', 'username', 'name', 'email',
        'mobile_no', 'line_no', 'profile', 'is_active', 'created_on', 'updated_on'
    )
    ordering = ('id',)  # ascending order by id

@admin.register(UniqueIdHeaderAll)
class UniqueIdHeaderAllAdmin(admin.ModelAdmin):
    list_display = ('table_name', 'id_for', 'prefix', 'last_id', 'created_on', 'modified_on')
    ordering = ('table_name',)  # ascending order by table_name