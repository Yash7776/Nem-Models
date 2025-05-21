from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db import IntegrityError
from .models import User_header_all, Profile_header_all

def user_detail(request, username):
    user = get_object_or_404(User_header_all, username=username, line_no=0)
    assignments = User_header_all.objects.filter(user_id=user.user_id).order_by('line_no')
    profiles = Profile_header_all.objects.all()
    return render(request, 'accounts/user_detail.html', {
        'user': user,
        'profiles': profiles,
        'active_profiles': user.get_active_profiles(),
        'assignments': assignments,
    })

def assign_profile(request, username):
    user = get_object_or_404(User_header_all, username=username, line_no=0)
    profile_id = request.GET.get('profile_id')
    if not profile_id:
        messages.error(request, "Please select a profile to assign.")
        return redirect('accounts:user_detail', username=username)
    profile = get_object_or_404(Profile_header_all, profile_id=profile_id)
    try:
        user.assign_profile(profile)
        messages.success(request, f"Profile {profile_id} assigned successfully.")
    except IntegrityError:
        messages.error(request, "Failed to assign profile due to a database error. Please try again.")
    return redirect('accounts:user_detail', username=username)

def assign_profile_from_edit(request, username):
    user = get_object_or_404(User_header_all, username=username, line_no=0)
    profile_id = request.GET.get('profile_id')
    if not profile_id:
        messages.error(request, "Please select a profile to assign.")
        return redirect('accounts:edit_user', user_id=user.id)
    profile = get_object_or_404(Profile_header_all, profile_id=profile_id)
    try:
        user.assign_profile(profile)
        messages.success(request, f"Profile {profile_id} assigned successfully.")
    except IntegrityError:
        messages.error(request, "Failed to assign profile due to a database error. Please try again.")
    return redirect('accounts:edit_user', user_id=user.id)

def toggle_profile_status(request, username, line_no):
    user = get_object_or_404(User_header_all, username=username, line_no=0)
    is_active = request.GET.get('is_active', 'true').lower() == 'true'
    redirect_to = request.GET.get('redirect_to', 'detail')
    user.set_profile_active(line_no, is_active)
    if redirect_to == 'edit':
        return redirect('accounts:edit_user', user_id=user.id)
    return redirect('accounts:user_detail', username=username)

def all_users(request):
    rows = User_header_all.objects.all().order_by('id')
    return render(request, 'accounts/all_users.html', {'rows': rows})

def create_user(request):
    profiles = Profile_header_all.objects.all()
    if request.method == 'POST':
        username = request.POST.get('username')
        name = request.POST.get('name')
        email = request.POST.get('email', '')
        password = request.POST.get('password')
        designation = request.POST.get('designation')
        mobile_no = request.POST.get('mobile_no', '')
        profile_id = request.POST.get('profile')

        user_id = User_header_all.get_or_assign_user_id(username)

        user = User_header_all.objects.create(
            user_id=user_id,
            line_no=0,
            name=name,
            email=email,
            username=username,
            password=password,
            designation=designation,
            mobile_no=mobile_no,
            profile=None,
            is_active=True
        )

        if profile_id:
            profile = get_object_or_404(Profile_header_all, profile_id=profile_id)
            try:
                user.assign_profile(profile)
            except IntegrityError:
                messages.error(request, "Failed to assign profile due to a database error. Please try again.")
                return redirect('accounts:user_detail', username=username)

        return redirect('accounts:user_detail', username=username)

    return render(request, 'accounts/create_user.html', {'profiles': profiles})

def edit_user(request, user_id):
    user = get_object_or_404(User_header_all, id=user_id)
    profiles = Profile_header_all.objects.all()
    assignments = User_header_all.objects.filter(user_id=user.user_id).order_by('line_no')

    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email', '')
        username = request.POST.get('username')
        password = request.POST.get('password')
        designation = request.POST.get('designation')
        mobile_no = request.POST.get('mobile_no', '')
        profile_id = request.POST.get('profile')
        
        user.name = name
        user.email = email
        user.password = password
        user.designation = designation
        user.mobile_no = mobile_no
        user.profile = Profile_header_all.objects.get(id=profile_id) if profile_id else None

        if user.username != username:
            existing_user = User_header_all.objects.filter(username=username).exclude(user_id=user.user_id).first()
            if existing_user:
                messages.error(request, f"Username '{username}' is already taken by another user.")
                return render(request, 'accounts/edit_user.html', {
                    'user': user,
                    'profiles': profiles,
                    'assignments': assignments,
                })

            User_header_all.objects.filter(user_id=user.user_id).update(username=username)
            user.username = username

        user.save()
        messages.success(request, "User details updated successfully.")
        return redirect('accounts:all_users')

    return render(request, 'accounts/edit_user.html', {
        'user': user,
        'profiles': profiles,
        'assignments': assignments,
    })

def deactivate_user(request, username):
    user = get_object_or_404(User_header_all, username=username, line_no=0)
    # Deactivate all rows for this user
    User_header_all.objects.filter(user_id=user.user_id).update(is_active=False)
    messages.success(request, f"User {username} has been deactivated.")
    return redirect('accounts:user_detail', username=username)