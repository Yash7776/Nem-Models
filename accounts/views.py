from django.shortcuts import render, get_object_or_404, redirect
from .models import User_header_all, Profile_header_all

def user_detail(request, username):
    user = get_object_or_404(User_header_all, username=username)
    profiles = Profile_header_all.objects.all()
    return render(request, 'accounts/user_detail.html', {
        'user': user,
        'profiles': profiles,
        'active_profiles': user.get_active_profiles(),
        'assignments': user.profile_assignments.all(),
    })

def assign_profile(request, username, profile_id):
    user = get_object_or_404(User_header_all, username=username)
    profile = get_object_or_404(Profile_header_all, profile_id=profile_id)
    user.assign_profile(profile)
    return redirect('accounts:user_detail', username=username)

def toggle_profile_status(request, username, line_no):
    user = get_object_or_404(User_header_all, username=username)
    is_active = request.GET.get('is_active', 'true').lower() == 'true'
    user.set_profile_active(line_no, is_active)
    return redirect('accounts:user_detail', username=username)