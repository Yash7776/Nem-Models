from django import forms
from django.contrib import admin
from .models import Profile_header_all, User_header_all, UniqueIdHeaderAll

class ProfileHeaderForm(forms.ModelForm):
    class Meta:
        model = Profile_header_all
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make profile_id field optional in the admin form
        self.fields['profile_id'].required = False

@admin.register(Profile_header_all)
class ProfileHeaderAdmin(admin.ModelAdmin):
    form = ProfileHeaderForm
    list_display = ('profile_id', 'profile_name', 'is_active')
    ordering = ('profile_id',)  # ascending order by profile_id

@admin.register(User_header_all)
class UserHeaderAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user_id', 'username', 'name', 'email', 'designation',
        'mobile_no', 'line_no', 'profile', 'is_active', 'created_on', 'updated_on'
    )
    ordering = ('id',)  # ascending order by id

@admin.register(UniqueIdHeaderAll)
class UniqueIdHeaderAllAdmin(admin.ModelAdmin):
    list_display = ('table_name', 'id_for', 'prefix', 'last_id', 'created_on', 'modified_on')
    ordering = ('table_name',)  # ascending order by table_name