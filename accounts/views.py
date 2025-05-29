from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from .models import User_header_all, Profile_header_all, StateHeaderAll, DistrictHeaderAll, TalukaHeaderAll, VillageHeaderAll, ProjectLocationDetailsAll

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
    return render(request, 'accounts/all_users.html', {
        'rows': rows,
        'user_type_choices': User_header_all.USER_TYPE_CHOICES,
    })

def create_user(request):
    profiles = Profile_header_all.objects.all()
    states = StateHeaderAll.objects.filter(st_status=True)
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
        st_id = request.POST.get('st_id')
        dist_id = request.POST.get('dist_id')
        tal_id = request.POST.get('tal_id')
        vil_id = request.POST.get('vil_id')

        existing_user = User_header_all.objects.filter(username=username).first()
        if existing_user:
            messages.error(request, "User Already Exists")
            return render(request, 'accounts/create_user.html', {
                'profiles': profiles,
                'user_type_choices': User_header_all.USER_TYPE_CHOICES,
                'states': states,
            })

        if mobile_no:
            existing_mobile = User_header_all.objects.filter(mobile_no=mobile_no).first()
            if existing_mobile:
                messages.error(request, f"Mobile number '{mobile_no}' is already taken by another user.")
                return render(request, 'accounts/create_user.html', {
                    'profiles': profiles,
                    'user_type_choices': User_header_all.USER_TYPE_CHOICES,
                    'states': states,
                })

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
                status=1,
                st_id=StateHeaderAll.objects.get(st_id=st_id) if st_id else None,
                dist_id=DistrictHeaderAll.objects.get(dist_id=dist_id) if dist_id else None,
                tal_id=TalukaHeaderAll.objects.get(tal_id=tal_id) if tal_id else None,
                vil_id=VillageHeaderAll.objects.get(vil_id=vil_id) if vil_id else None,
            )

            # Validate location against project_id
            if vil_id and project_id_dict:
                project_ids = []
                for projects in project_id_dict.values():
                    project_ids.extend([int(pid) for pid in projects if pid.isdigit()])
                if project_ids:
                    valid_location = ProjectLocationDetailsAll.objects.filter(
                        project_id__in=project_ids,
                        vil_id=vil_id,
                        status=True
                    ).exists()
                    if not valid_location:
                        messages.error(request, "Selected village is not associated with the specified projects.")
                        return render(request, 'accounts/create_user.html', {
                            'profiles': profiles,
                            'user_type_choices': User_header_all.USER_TYPE_CHOICES,
                            'states': states,
                        })

            user.full_clean()
            user.save()

            if profile_id:
                profile = get_object_or_404(Profile_header_all, profile_id=profile_id)
                try:
                    user.assign_profile(profile)
                except IntegrityError:
                    messages.error(request, "Failed to assign profile due to a database error. Please try again.")
                    return redirect('user_detail', username=username)

            messages.success(request, f"User {username} created successfully.")
            return redirect('user_detail', username=username)

        except ValidationError as e:
            for field, errors in e.message_dict.items():
                for error in errors:
                    messages.error(request, f"{field.capitalize()}: {error}")
            return render(request, 'accounts/create_user.html', {
                'profiles': profiles,
                'user_type_choices': User_header_all.USER_TYPE_CHOICES,
                'states': states,
            })
        except IntegrityError:
            messages.error(request, "User Already Exists")
            return render(request, 'accounts/create_user.html', {
                'profiles': profiles,
                'user_type_choices': User_header_all.USER_TYPE_CHOICES,
                'states': states,
            })

    return render(request, 'accounts/create_user.html', {
        'profiles': profiles,
        'user_type_choices': User_header_all.USER_TYPE_CHOICES,
        'states': states,
    })

def edit_user(request, user_id):
    user = get_object_or_404(User_header_all, id=user_id)
    profiles = Profile_header_all.objects.all()
    assignments = User_header_all.objects.filter(user_id=user.user_id).order_by('line_no')
    states = StateHeaderAll.objects.filter(st_status=True)

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
        st_id = request.POST.get('st_id')
        dist_id = request.POST.get('dist_id')
        tal_id = request.POST.get('tal_id')
        vil_id = request.POST.get('vil_id')

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
                        'states': states,
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
            user.st_id = StateHeaderAll.objects.get(st_id=st_id) if st_id else None
            user.dist_id = DistrictHeaderAll.objects.get(dist_id=dist_id) if dist_id else None
            user.tal_id = TalukaHeaderAll.objects.get(tal_id=tal_id) if tal_id else None
            user.vil_id = VillageHeaderAll.objects.get(vil_id=vil_id) if vil_id else None

            # Validate location against project_id
            if vil_id:
                project_ids = []
                for projects in user.project_id.values():
                    project_ids.extend([int(pid) for pid in projects if pid.isdigit()])
                if project_ids:
                    valid_location = ProjectLocationDetailsAll.objects.filter(
                        project_id__in=project_ids,
                        vil_id=vil_id,
                        status=True
                    ).exists()
                    if not valid_location:
                        messages.error(request, "Selected village is not associated with the user's projects.")
                        return render(request, 'accounts/edit_user.html', {
                            'user': user,
                            'profiles': profiles,
                            'assignments': assignments,
                            'user_type_choices': User_header_all.USER_TYPE_CHOICES,
                            'states': states,
                        })

            if user.username != username:
                existing_user = User_header_all.objects.filter(username=username).exclude(id=user_id).first()
                if existing_user:
                    messages.error(request, f"Username '{username}' is already taken by another user.")
                    return render(request, 'accounts/edit_user.html', {
                        'user': user,
                        'profiles': profiles,
                        'assignments': assignments,
                        'user_type_choices': User_header_all.USER_TYPE_CHOICES,
                        'states': states,
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
                'states': states,
            })

    return render(request, 'accounts/edit_user.html', {
        'user': user,
        'profiles': profiles,
        'assignments': assignments,
        'user_type_choices': User_header_all.USER_TYPE_CHOICES,
        'states': states,
    })

def toggle_user_status(request, username):
    user = get_object_or_404(User_header_all, username=username, line_no=0)
    activate = request.GET.get('activate', 'false').lower() == 'true'
    if activate:
        User_header_all.objects.filter(user_id=user.user_id).update(status=1, deactivated_on=None)
        messages.success(request, f"User {username} has been activated.")
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

def get_districts(request, state_id):
    districts = DistrictHeaderAll.objects.filter(st_id=state_id, status=True).values('dist_id', 'dist_name')
    return JsonResponse({'districts': list(districts)})

def get_talukas(request, district_id):
    talukas = TalukaHeaderAll.objects.filter(dist_id=district_id, status=True).values('tal_id', 'tal_name')
    return JsonResponse({'talukas': list(talukas)})

def get_villages(request, taluka_id):
    villages = VillageHeaderAll.objects.filter(tal_id=taluka_id, status=True).values('vil_id', 'name')
    return JsonResponse({'villages': list(villages)})