from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db import IntegrityError
from django.core.exceptions import ValidationError
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
        return redirect('user_detail', username=username)
    profile = get_object_or_404(Profile_header_all, profile_id=profile_id)
    try:
        user.assign_profile(profile)
        messages.success(request, f"Profile {profile_id} assigned successfully.")
    except ValidationError as e:
        messages.error(request, f"Failed to assign profile: {str(e)}")
    except IntegrityError as e:
        messages.error(request, "Failed to assign profile due to a database error. Please try again.")
    return redirect('user_detail', username=username)

def assign_profile_from_edit(request, username):
    user = get_object_or_404(User_header_all, username=username, line_no=0)
    profile_id = request.GET.get('profile_id')
    if not profile_id:
        messages.error(request, "Please select a profile to assign.")
        return redirect('edit_user', user_id=user.id)
    profile = get_object_or_404(Profile_header_all, profile_id=profile_id)
    try:
        user.assign_profile(profile)
        messages.success(request, f"Profile {profile_id} assigned successfully.")
    except ValidationError as e:
        messages.error(request, f"Failed to assign profile: {str(e)}")
    except IntegrityError as e:
        messages.error(request, "Failed to assign profile due to a database error. Please try again.")
    return redirect('edit_user', user_id=user.id)

def toggle_profile_status(request, username, line_no):
    user = get_object_or_404(User_header_all, username=username, line_no=0)
    is_active = request.GET.get('is_active', 'true').lower() == 'true'
    redirect_to = request.GET.get('redirect_to', 'detail')
    user.set_profile_active(line_no, is_active)
    if redirect_to == 'edit':
        return redirect('edit_user', user_id=user.id)
    return redirect('user_detail', username=username)

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

        # Check if a user with this username already exists
        existing_user = User_header_all.objects.filter(username=username).first()
        if existing_user:
            messages.error(request, "User Already Exists")
            return redirect('create_user')

        # Check if the mobile number is already used by another user_id
        if mobile_no:
            existing_mobile = User_header_all.objects.filter(mobile_no=mobile_no).first()
            if existing_mobile:
                messages.error(request, f"Mobile number '{mobile_no}' is already taken by another user.")
                return redirect('create_user')

        user_id = User_header_all.get_or_assign_user_id(username)

        try:
            user = User_header_all(
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
            user.full_clean()  # Run model validation
            user.save()

            if profile_id:
                profile = get_object_or_404(Profile_header_all, profile_id=profile_id)
                try:
                    user.assign_profile(profile)
                except IntegrityError:
                    messages.error(request, "Failed to assign profile due to a database error. Please try again.")
                    return redirect('user_detail', username=username)

            return redirect('user_detail', username=username)

        except ValidationError as e:
            for field, errors in e.message_dict.items():
                for error in errors:
                    messages.error(request, f"{field.capitalize()}: {error}")
            return redirect('create_user')
        except IntegrityError:
            messages.error(request, "User Already Exists")
            return redirect('create_user')

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

        try:
            # Check if the mobile number is already used by another user_id
            if mobile_no and mobile_no != user.mobile_no:
                existing_mobile = User_header_all.objects.filter(mobile_no=mobile_no).exclude(user_id=user.user_id).first()
                if existing_mobile:
                    messages.error(request, f"Mobile number '{mobile_no}' is already taken by another user.")
                    return render(request, 'accounts/edit_user.html', {
                        'user': user,
                        'profiles': profiles,
                        'assignments': assignments,
                    })

            user.name = name
            user.email = email
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

            # Update password only if a new one is provided
            if password:
                user.password = password

            user.full_clean()
            user.save()
            messages.success(request, "User details updated successfully.")
            return redirect('all_users')

        except ValidationError as e:
            for field, errors in e.message_dict.items():
                for error in errors:
                    messages.error(request, f"{field.capitalize()}: {error}")
            return render(request, 'accounts/edit_user.html', {
                'user': user,
                'profiles': profiles,
                'assignments': assignments,
            })

    return render(request, 'accounts/edit_user.html', {
        'user': user,
        'profiles': profiles,
        'assignments': assignments,
    })

def toggle_user_status(request, username):
    user = get_object_or_404(User_header_all, username=username, line_no=0)
    activate = request.GET.get('activate', 'false').lower() == 'true'
    if activate:
        User_header_all.objects.filter(user_id=user.user_id).update(is_active=True)
        messages.success(request, f"User {username} has been activated.")
    else:
        User_header_all.objects.filter(user_id=user.user_id).update(is_active=False)
        messages.success(request, f"User {username} has been deactivated.")
    return redirect('user_detail', username=username)

def users_summary(request):
    # Get only the base records (line_no=0) for each user
    users = User_header_all.objects.filter(line_no=0).order_by('user_id')
    
    # Prepare a list of users with their activated and deactivated profiles
    user_data = []
    for user in users:
        assignments = User_header_all.objects.filter(user_id=user.user_id, profile__isnull=False)
        activated_profiles = [assignment.profile.profile_id for assignment in assignments if assignment.is_active]
        deactivated_profiles = [assignment.profile.profile_id for assignment in assignments if not assignment.is_active]
        user_data.append({
            'user': user,
            'activated_profiles': activated_profiles,
            'deactivated_profiles': deactivated_profiles,
        })
    
    return render(request, 'accounts/users_summary.html', {'user_data': user_data})