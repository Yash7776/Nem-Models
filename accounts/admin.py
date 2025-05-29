from django.contrib import admin
from .models import (
    StateHeaderAll, DistrictHeaderAll, TalukaHeaderAll, VillageHeaderAll,
    ProjectLocationDetailsAll, User_header_all, Profile_header_all,
    Department, Project, UniqueIdHeaderAll
)

@admin.register(StateHeaderAll)
class StateHeaderAllAdmin(admin.ModelAdmin):
    list_display = ('st_id', 'st_name', 'st_status', 'st_inserted_on')
    search_fields = ('st_name',)
    list_filter = ('st_status',)
    ordering = ('st_name',)

@admin.register(DistrictHeaderAll)
class DistrictHeaderAllAdmin(admin.ModelAdmin):
    list_display = ('dist_id', 'dist_name', 'st_id', 'status', 'inserted')
    search_fields = ('dist_name',)
    list_filter = ('status', 'st_id')
    autocomplete_fields = ['st_id']

@admin.register(TalukaHeaderAll)
class TalukaHeaderAllAdmin(admin.ModelAdmin):
    list_display = ('tal_id', 'tal_name', 'dist_id', 'st_id', 'status', 'inserted')
    search_fields = ('tal_name',)
    list_filter = ('status', 'dist_id', 'st_id')
    autocomplete_fields = ['dist_id', 'st_id']

@admin.register(VillageHeaderAll)
class VillageHeaderAllAdmin(admin.ModelAdmin):
    list_display = ('vil_id', 'name', 'tal_id', 'dist_id', 'st_id', 'status', 'inserted')
    search_fields = ('name',)
    list_filter = ('status', 'tal_id', 'dist_id', 'st_id')
    autocomplete_fields = ['tal_id', 'dist_id', 'st_id']

@admin.register(ProjectLocationDetailsAll)
class ProjectLocationDetailsAllAdmin(admin.ModelAdmin):
    list_display = ('pl_id', 'project_id', 'get_location_type', 'st_id', 'dist_id', 'tal_id', 'vil_id', 'status', 'inserted')
    search_fields = ('project_id',)
    list_filter = ('pl_location_type', 'status', 'st_id', 'dist_id', 'tal_id', 'vil_id')
    autocomplete_fields = ['st_id', 'dist_id', 'tal_id', 'vil_id']

    def get_location_type(self, obj):
        return obj.get_pl_location_type_display()
    get_location_type.short_description = 'Location Type'

# Existing model registrations (if any)
@admin.register(User_header_all)
class UserHeaderAllAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'username', 'full_name', 'user_type', 'status', 'inserted_on')
    search_fields = ('username', 'full_name', 'email')
    list_filter = ('user_type', 'status')
    autocomplete_fields = ['profile_id', 'st_id', 'dist_id', 'tal_id', 'vil_id']

@admin.register(Profile_header_all)
class ProfileHeaderAllAdmin(admin.ModelAdmin):
    list_display = ('profile_id', 'profile_name', 'p_status', 'pro_inserted_on')
    search_fields = ('profile_id', 'profile_name')
    list_filter = ('p_status',)

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('dept_id', 'name')
    search_fields = ('dept_id', 'name')

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('project_id', 'project_name', 'department')
    search_fields = ('project_id', 'name')
    list_filter = ('department',)
    autocomplete_fields = ['department']

@admin.register(UniqueIdHeaderAll)
class UniqueIdHeaderAllAdmin(admin.ModelAdmin):
    list_display = ('table_name', 'id_for', 'prefix', 'last_id', 'created_on')
    search_fields = ('table_name', 'id_for')