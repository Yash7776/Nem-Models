from django.shortcuts import render, get_object_or_404, redirect
from .models import User_header_all, Profile_header_all

def get_all_denormalized_rows():
    all_rows = []
    current_id = 1
    for user in User_header_all.objects.all():
        denormalized_rows = user.get_denormalized_data()
        for row in denormalized_rows:
            row["id"] = current_id
            all_rows.append(row)
            current_id += 1
    return all_rows

def user_detail(request, username):
    user = get_object_or_404(User_header_all, username=username)
    profiles = Profile_header_all.objects.all()
    user_rows = user.get_denormalized_data()
    return render(request, 'accounts/user_detail.html', {
        'user': user,
        'profiles': profiles,
        'active_profiles': user.get_active_profiles(),
        'assignments': user_rows,
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

def all_users(request):
    denormalized_rows = get_all_denormalized_rows()
    return render(request, 'accounts/all_users.html', {'rows': denormalized_rows})