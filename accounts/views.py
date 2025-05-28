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
        'user_type_choices': User_header_all.USER_TYPE_CHOICES,
    })

def assign_profile(request, username):
    user = get_object_or_404(User_header_all, username=username, line_no=0)
    profile_id = request.GET.get('profile_id')
    if not profile_id:
        messages.error(request, "Please select a profile to assign Profile ID {profile_id} assigned successfully.")
        return redirect('user_detail', user_id=user_id)
    profile = get_object_or_404(Profile_header_all, profile_id=profile_id)
    try:
        profile = User_header_all.objects.profile_id(profile_id)
        messages.success(request, f"Profile {profile_id} assigned successfully.")
    except ValidationError as e:
        messages.error(request, f"Failed to assign profile: {str(e)}")
    except IntegrityError as e:
        messages.error(request, "Failed to assign profile due to a database error. Please try again.")
    return redirect('user_detail', profile_id=profile_id)

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
    return render(request, 'accounts/all_users.html', {
        'rows': rows,
        'user_type_choices': User_header_all.USER_TYPE_CHOICES,
    })

def create_user(request):
    profiles = Profile_header_all.objects.all()
    if request.method == 'POST':
        username = request.POST.get('username')
        full_name = request.POST.get('full_name')
        email = request.POST.get('email', '')
        password = request.POST.get('password')
        mobile_no = request.POST.get('mobile_no', '')
        user_type = request.POST.get('user_type')
        dept_id = request.POST.get('dept_id', '')
        project_ids = request.POST.get('project_ids', '')
        profile_id = request.POST.get('profile')

        existing_user = User_header_all.objects.filter(username=username).first()
        if existing_user:
            messages.error(request, "User Already Exists")
            return redirect('create_user')

        if mobile_no:
            existing_mobile = User_header_all.objects.filter(mobile_no=mobile_no).first()
            if existing_mobile:
                messages.error(request, f"Mobile number '{mobile_no}' is already taken by another user.")
                return redirect('create_user')

        user_id = User_header_all.get_or_assign_user_id(username)

        try:
            project_id_dict = {}
            if dept_id and project_ids:
                project_id_list = [pid.strip() for pid in project_ids.split(',') if pid.strip()]
                project_id_dict[dept_id] = project_id_list

            user = User_header_all(
                user_id=user_id,
                line_no=0,
                full_name=full_name,
                email=email,
                username=username,
                password=password,
                mobile_no=mobile_no,
                profile_id=None,
                project_id=project_id_dict,
                user_type=int(user_type),
                status=1
            )
            user.full_clean()
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

    return render(request, 'accounts/create_user.html', {
        'profiles': profiles,
        'user_type_choices': User_header_all.USER_TYPE_CHOICES,
    })

def edit_user(request, user_id):
    user = get_object_or_404(User_header_all, id=user_id)
    profiles = Profile_header_all.objects.all()
    assignments = User_header_all.objects.filter(user_id=user.user_id).order_by('line_no')

    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email', '')
        username = request.POST.get('username')
        password = request.POST.get('password')
        mobile_no = request.POST.get('mobile_no', '')
        user_type = request.POST.get('user_type')
        dept_id = request.POST.get('dept_id', '')
        project_ids = request.POST.get('project_ids', '')
        profile_id = request.POST.get('profile')

        try:
            if mobile_no and mobile_no != user.mobile_no:
                existing_mobile = User_header_all.objects.filter(mobile_no=mobile_no).exclude(user_id=user.user_id).first()
                if existing_mobile:
                    messages.error(request, f"Mobile number '{mobile_no}' is already taken by another user.")
                    return render(request, 'accounts/edit_user.html', {
                        'user': user,
                        'profiles': profiles,
                        'assignments': assignments,
                        'user_type_choices': User_header_all.USER_TYPE_CHOICES,
                    })

            user.full_name = full_name
            user.email = email
            user.user_type = int(user_type)

            project_id_dict = user.project_id
            if dept_id and project_ids:
                project_id_list = [pid.strip() for pid in project_ids.split(',') if pid.strip()]
                project_id_dict[dept_id] = project_id_list
            user.project_id = project_id_dict

            user.mobile_no = mobile_no
            user.profile_id = Profile_header_all.objects.get(id=profile_id) if profile_id else None

            if user.username != username:
                existing_user = User_header_all.objects.filter(username=username).exclude(id=user_id).first()
                if existing_user:
                    messages.error(request, f"Username '{username}' is already taken by another user.")
                    return render(request, 'accounts/edit_user.html', {
                        'user': user,
                        'profiles': profiles,
                        'assignments': assignments,
                        'user_type_choices': User_header_all.USER_TYPE_CHOICES,
                    })

                User_header_all.objects.filter(user_id=user.user_id).update(username=username)
                user.username = username

            if password:
                user.password = password

            user.full_clean()
            user.save()
            messages.success(request, "User details updated successfully.")
            return redirect('all_users')

        except ValidationError as e:
            for field, errors in e.message_dict.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
            return render(request, 'accounts/edit_user.html', {
                'user': user,
                'profiles': profiles,
                'assignments': assignments,
                'user_type_choices': User_header_all.USER_TYPE_CHOICES,
            })

    return render(request, 'accounts/edit_user.html', {
        'user': user,
        'profiles': profiles,
        'assignments': assignments,
        'user_type_choices': User_header_all.USER_TYPE_CHOICES,
    })

def toggle_user_status(request, username):
    user = get_object_or_404(User_header_all, username=username, line_no=0)
    activate = request.GET.get('activate', 'false').lower() == 'true'
    if activate:
        User_header_all.objects.filter(user_id=user.user_id).update(status=1, deactivated_on=None)
        messages.success(request.SUCCESS, f"User {username} has been activated.")
    else:
        User_header_all.objects.filter(user_id=user.user_id).update(status=0, deactivated_on=timezone.now())
        messages.success(request, f"User {username} has been deactivated.")
    return redirect('user_detail', username=username)

def users_summary(request):
    users = User_header_all.objects.filter(line_no=0).order_by('user_id')
    
    user_data = []
    for user in users:
        assignments = User_header_all.objects.filter(user_id=user.user_id, profile_id__isnull=False)
        activated_profiles = [assignment.profile_id.profile_id for assignment in assignments if assignment.status == 1]
        deactivated_profiles = [assignment.profile_id.profile_id for assignment in assignments if assignment.status == 0]
        user_data.append({
            'user': user,
            'activated_profiles': activated_profiles,
            'deactivated_profiles': deactivated_profiles,
        })
    
    return render(request, 'accounts/users_summary.html', {
        'user_data': user_data,
        'user_type_choices': User_header_all.USER_TYPE_CHOICES,
    })