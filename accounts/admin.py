from django import forms
from django.contrib import admin
from .models import Profile_header_all, User_header_all, UniqueIdHeaderAll

class ProfileHeaderForm(forms.ModelForm):
    class Meta:
        model = Profile_header_all
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['profile_id'].required = False

class UserHeaderForm(forms.ModelForm):
    class Meta:
        model = User_header_all
        fields = '__all__'

@admin.register(Profile_header_all)
class ProfileHeaderAdmin(admin.ModelAdmin):
    form = ProfileHeaderForm
    list_display = ('profile_id', 'profile_name', 'p_status', 'pro_inserted_on', 'pro_deactivated_on')
    ordering = ('profile_id',)

@admin.register(User_header_all)
class UserHeaderAdmin(admin.ModelAdmin):
    form = UserHeaderForm
    list_display = (
        'id', 'user_id', 'username', 'full_name', 'email',
        'mobile_no', 'line_no', 'profile_id', 'status', 'inserted_on'
    )
    ordering = ('id',)

@admin.register(UniqueIdHeaderAll)
class UniqueIdHeaderAllAdmin(admin.ModelAdmin):
    list_display = ('table_name', 'id_for', 'prefix', 'last_id', 'created_on', 'modified_on')
    ordering = ('table_name',)