from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.db.models import Q
from .models import (
    User_header_all, Profile_header_all, StateHeaderAll, DistrictHeaderAll,
    TalukaHeaderAll, VillageHeaderAll, Project, ProjectLocationDetailsAll, Department
)
from django.utils import timezone

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
    departments = Department.objects.all()
    projects = Project.objects.filter(project_status=1)  # Only active projects
    if request.method == 'POST':
        username = request.POST.get('username')
        full_name = request.POST.get('full_name')
        email = request.POST.get('email', '')
        password = request.POST.get('password')
        mobile_no = request.POST.get('mobile_no', '')
        user_type = request.POST.get('user_type')
        dept_id = request.POST.get('dept_id', '')
        project_ids = request.POST.getlist('project_ids[]')  # Get list of selected project IDs
        profile_ids = request.POST.getlist('profile_ids[]')  # Get list of selected profile IDs

        existing_user = User_header_all.objects.filter(username=username).first()
        if existing_user:
            messages.error(request, "User Already Exists")
            return render(request, 'accounts/create_user.html', {
                'profiles': profiles,
                'departments': departments,
                'projects': projects,
                'user_type_choices': User_header_all.USER_TYPE_CHOICES,
            })

        if mobile_no:
            existing_mobile = User_header_all.objects.filter(mobile_no=mobile_no).first()
            if existing_mobile:
                messages.error(request, f"Mobile number '{mobile_no}' is already taken by another user.")
                return render(request, 'accounts/create_user.html', {
                    'profiles': profiles,
                    'departments': departments,
                    'projects': projects,
                    'user_type_choices': User_header_all.USER_TYPE_CHOICES,
                })

        user_id = User_header_all.get_or_assign_user_id(username)

        try:
            project_id_dict = {}
            if dept_id and project_ids:
                valid_projects = Project.objects.filter(department__dept_id=dept_id, project_id__in=project_ids)
                valid_project_ids = set(valid_projects.values_list('project_id', flat=True))
                invalid_projects = [pid for pid in project_ids if pid not in valid_project_ids]
                if invalid_projects:
                    messages.error(request, f"Projects {', '.join(invalid_projects)} do not belong to department {dept_id}.")
                    return render(request, 'accounts/create_user.html', {
                        'profiles': profiles,
                        'departments': departments,
                        'projects': projects,
                        'user_type_choices': User_header_all.USER_TYPE_CHOICES,
                    })
                project_id_dict[dept_id] = project_ids

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
            )

            user.full_clean()
            user.save()

            if profile_ids:
                for profile_id in profile_ids:
                    profile = get_object_or_404(Profile_header_all, profile_id=profile_id)
                    try:
                        user.assign_profile(profile)
                    except IntegrityError:
                        messages.error(request, f"Failed to assign profile {profile_id} due to a database error.")
                        return redirect('user_detail', username=username)

            messages.success(request, f"User {username} created successfully.")
            return redirect('user_detail', username=username)

        except ValidationError as e:
            for field, errors in e.message_dict.items():
                for error in errors:
                    messages.error(request, f"{field.capitalize()}: {error}")
            return render(request, 'accounts/create_user.html', {
                'profiles': profiles,
                'departments': departments,
                'projects': projects,
                'user_type_choices': User_header_all.USER_TYPE_CHOICES,
            })
        except IntegrityError:
            messages.error(request, "User Already Exists")
            return render(request, 'accounts/create_user.html', {
                'profiles': profiles,
                'departments': departments,
                'projects': projects,
                'user_type_choices': User_header_all.USER_TYPE_CHOICES,
            })

    return render(request, 'accounts/create_user.html', {
        'profiles': profiles,
        'departments': departments,
        'projects': projects,
        'user_type_choices': User_header_all.USER_TYPE_CHOICES,
    })

def get_projects_by_department(request, dept_id):
    try:
        projects = Project.objects.filter(department__dept_id=dept_id, project_status=1).values('project_id', 'project_name')
        return JsonResponse({'projects': list(projects)})
    except Department.DoesNotExist:
        return JsonResponse({'projects': [], 'error': 'Department not found'}, status=404)
    except Exception as e:
        return JsonResponse({'projects': [], 'error': str(e)}, status=500)

def edit_user(request, user_id):
    user = get_object_or_404(User_header_all, id=user_id)
    profiles = Profile_header_all.objects.all()
    departments = Department.objects.all()
    assignments = User_header_all.objects.filter(user_id=user.user_id).order_by('line_no')

    # Extract dept_id and project_ids
    dept_id = next(iter(user.project_id), '') if user.project_id else ''
    project_ids = user.project_id.get(dept_id, []) if dept_id else []
    selected_project_names = []
    if project_ids:
        selected_projects = Project.objects.filter(project_id__in=project_ids).values('project_name')
        selected_project_names = [p['project_name'] for p in selected_projects]

    # Get active profile IDs
    active_profile_ids = [p.profile_id for p in user.get_active_profiles()]

    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email', '')
        username = request.POST.get('username')
        password = request.POST.get('password')
        mobile_no = request.POST.get('mobile_no', '')
        user_type = request.POST.get('user_type')
        dept_id = request.POST.get('dept_id', '')
        project_ids = request.POST.getlist('project_ids[]')  # Get list from checkbox dropdown
        profile_ids = request.POST.getlist('profile_ids[]')  # Get list of selected profile IDs

        try:
            if mobile_no and mobile_no != user.mobile_no:
                existing_mobile = User_header_all.objects.filter(mobile_no=mobile_no).exclude(user_id=user.user_id).first()
                if existing_mobile:
                    messages.error(request, f"Mobile number '{mobile_no}' is already taken by another user.")
                    return render(request, 'accounts/edit_user.html', {
                        'user': user,
                        'profiles': profiles,
                        'departments': departments,
                        'assignments': assignments,
                        'user_type_choices': User_header_all.USER_TYPE_CHOICES,
                        'dept_id': dept_id,
                        'selected_project_ids': project_ids,
                        'selected_project_names': selected_project_names,
                        'active_profile_ids': active_profile_ids,
                    })

            user.full_name = full_name
            user.email = email
            user.user_type = int(user_type)

            project_id_dict = {}
            if dept_id and project_ids:
                valid_projects = Project.objects.filter(department__dept_id=dept_id, project_id__in=project_ids)
                valid_project_ids = set(valid_projects.values_list('project_id', flat=True))
                invalid_projects = [pid for pid in project_ids if pid not in valid_project_ids]
                if invalid_projects:
                    messages.error(request, f"Projects {', '.join(invalid_projects)} do not belong to department {dept_id}.")
                    return render(request, 'accounts/edit_user.html', {
                        'user': user,
                        'profiles': profiles,
                        'departments': departments,
                        'assignments': assignments,
                        'user_type_choices': User_header_all.USER_TYPE_CHOICES,
                        'dept_id': dept_id,
                        'selected_project_ids': project_ids,
                        'selected_project_names': selected_project_names,
                        'active_profile_ids': active_profile_ids,
                    })
                project_id_dict[dept_id] = project_ids
            user.project_id = project_id_dict

            user.mobile_no = mobile_no

            if user.username != username:
                existing_user = User_header_all.objects.filter(username=username).exclude(id=user_id).first()
                if existing_user:
                    messages.error(request, f"Username '{username}' is already taken by another user.")
                    return render(request, 'accounts/edit_user.html', {
                        'user': user,
                        'profiles': profiles,
                        'departments': departments,
                        'assignments': assignments,
                        'user_type_choices': User_header_all.USER_TYPE_CHOICES,
                        'dept_id': dept_id,
                        'selected_project_ids': project_ids,
                        'selected_project_names': selected_project_names,
                        'active_profile_ids': active_profile_ids,
                    })

                User_header_all.objects.filter(user_id=user.user_id).update(username=username)
                user.username = username

            if password:
                user.password = password

            user.full_clean()
            user.save()

            # Clear existing profile assignments (except line_no=0)
            User_header_all.objects.filter(user_id=user.user_id, profile_id__isnull=False).delete()
            # Assign new profiles
            if profile_ids:
                for profile_id in profile_ids:
                    profile = get_object_or_404(Profile_header_all, profile_id=profile_id)
                    try:
                        user.assign_profile(profile)
                    except IntegrityError:
                        messages.error(request, f"Failed to assign profile {profile_id} due to a database error.")
                        return render(request, 'accounts/edit_user.html', {
                            'user': user,
                            'profiles': profiles,
                            'departments': departments,
                            'assignments': assignments,
                            'user_type_choices': User_header_all.USER_TYPE_CHOICES,
                            'dept_id': dept_id,
                            'selected_project_ids': project_ids,
                            'selected_project_names': selected_project_names,
                            'active_profile_ids': active_profile_ids,
                        })

            messages.success(request, "User details updated successfully.")
            return redirect('all_users')

        except ValidationError as e:
            for field, errors in e.message_dict.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
            return render(request, 'accounts/edit_user.html', {
                'user': user,
                'profiles': profiles,
                'departments': departments,
                'assignments': assignments,
                'user_type_choices': User_header_all.USER_TYPE_CHOICES,
                'dept_id': dept_id,
                'selected_project_ids': project_ids,
                'selected_project_names': selected_project_names,
                'active_profile_ids': active_profile_ids,
            })

    return render(request, 'accounts/edit_user.html', {
        'user': user,
        'profiles': profiles,
        'departments': departments,
        'assignments': assignments,
        'user_type_choices': User_header_all.USER_TYPE_CHOICES,
        'dept_id': dept_id,
        'selected_project_ids': project_ids,
        'selected_project_names': selected_project_names,
        'active_profile_ids': active_profile_ids,
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

def manage_locations(request):
    return render(request, 'accounts/manage_locations.html', {})

def project_combination(request):
    projects = Project.objects.filter(project_status=1)
    return render(request, 'accounts/Project_Combination.html', {
        'projects': projects,
        'location_type_choices': ProjectLocationDetailsAll.LOCATION_TYPE_CHOICES,
    })

def save_project_location(request):
    if request.method != 'POST':
        return redirect('manage_locations')

    project_id = request.POST.get('project_id')
    pl_location_type = request.POST.get('pl_location_type')
    state_id = request.POST.get('state_id')
    district_id = request.POST.get('district_id')
    taluka_id = request.POST.get('taluka_id')
    village_id = request.POST.get('village_id')

    if not project_id or not pl_location_type:
        messages.error(request, "Project ID and Location Type are required.")
        return redirect('manage_locations')

    try:
        project = get_object_or_404(Project, project_id=project_id)
        pl_location_type = int(pl_location_type)

        location_data = {
            'project_id': project,
            'pl_location_type': pl_location_type,
            'status': True,
        }

        if pl_location_type == 1:
            if not state_id:
                messages.error(request, "State ID is required for State location type.")
                return redirect('manage_locations')
            location_data['st_id'] = get_object_or_404(StateHeaderAll, st_id=state_id)
        elif pl_location_type == 2:
            if not district_id:
                messages.error(request, "District ID is required for District location type.")
                return redirect('manage_locations')
            district = get_object_or_404(DistrictHeaderAll, dist_id=district_id)
            location_data['st_id'] = district.st_id
            location_data['dist_id'] = district
        elif pl_location_type == 3:
            if not taluka_id:
                messages.error(request, "Taluka ID is required for Taluka location type.")
                return redirect('manage_locations')
            taluka = get_object_or_404(TalukaHeaderAll, tal_id=taluka_id)
            location_data['st_id'] = taluka.st_id
            location_data['dist_id'] = taluka.dist_id
            location_data['tal_id'] = taluka
        elif pl_location_type == 4:
            if not village_id:
                messages.error(request, "Village ID is required for Village location type.")
                return redirect('manage_locations')
            village = get_object_or_404(VillageHeaderAll, vil_id=village_id)
            location_data['st_id'] = village.st_id
            location_data['dist_id'] = village.dist_id
            location_data['tal_id'] = village.tal_id
            location_data['vil_id'] = village
        else:
            messages.error(request, "Invalid location type.")
            return redirect('manage_locations')

        try:
            project_location = ProjectLocationDetailsAll.objects.create(**location_data)
            project_location.full_clean()
            project_location.save()
            messages.success(request, "Project location saved successfully.")
        except (ValidationError, IntegrityError) as e:
            messages.error(request, f"Failed to save project location: {str(e)}")
        
        return redirect('manage_locations')

    except Exception as e:
        messages.error(request, f"Error saving project location: {str(e)}")
        return redirect('manage_locations')

def save_project_combination(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

    project_id = request.POST.get('project_id')
    pl_location_type = request.POST.get('pl_location_type')
    state_id = request.POST.get('state_id')
    district_id = request.POST.get('district_id')
    taluka_id = request.POST.get('taluka_id')
    village_id = request.POST.get('village_id')

    if not project_id or not pl_location_type:
        return JsonResponse({'status': 'error', 'message': 'Project ID and Combination Type are required'}, status=400)

    try:
        project = get_object_or_404(Project, project_id=project_id)
        pl_location_type = int(pl_location_type)

        combination_data = {
            'project_id': project,
            'pl_location_type': pl_location_type,
            'status': True,
        }

        if pl_location_type == 1:
            if not state_id:
                return JsonResponse({'status': 'error', 'message': 'State ID is required for State combination type'}, status=400)
            combination_data['st_id'] = get_object_or_404(StateHeaderAll, st_id=state_id)
        elif pl_location_type == 2:
            if not district_id:
                return JsonResponse({'status': 'error', 'message': 'District ID is required for District combination type'}, status=400)
            district = get_object_or_404(DistrictHeaderAll, dist_id=district_id)
            combination_data['st_id'] = district.st_id
            combination_data['dist_id'] = district
        elif pl_location_type == 3:
            if not taluka_id:
                return JsonResponse({'status': 'error', 'message': 'Taluka ID is required for Taluka combination type'}, status=400)
            taluka = get_object_or_404(TalukaHeaderAll, tal_id=taluka_id)
            combination_data['st_id'] = taluka.st_id
            combination_data['dist_id'] = taluka.dist_id
            combination_data['tal_id'] = taluka
        elif pl_location_type == 4:
            if not village_id:
                return JsonResponse({'status': 'error', 'message': 'Village ID is required for Village combination type'}, status=400)
            village = get_object_or_404(VillageHeaderAll, vil_id=village_id)
            combination_data['st_id'] = village.st_id
            combination_data['dist_id'] = village.dist_id
            combination_data['tal_id'] = village.tal_id
            combination_data['vil_id'] = village
        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid combination type'}, status=400)

        try:
            project_combination = ProjectLocationDetailsAll.objects.create(**combination_data)
            project_combination.full_clean()
            project_combination.save()
            return JsonResponse({'status': 'success', 'message': 'Project combination saved successfully'})
        except (ValidationError, IntegrityError) as e:
            return JsonResponse({'status': 'error', 'message': f'Failed to save project combination: {str(e)}'}, status=400)
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Error saving project combination: {str(e)}'}, status=500)

def get_districts(request, state_id):
    districts = DistrictHeaderAll.objects.filter(st_id=state_id, status=True).values('dist_id', 'dist_name')
    return JsonResponse({'district': list(districts)})

def get_talukas(request, district_id):
    talukas = TalukaHeaderAll.objects.filter(dist_id=district_id, status=True).values('tal_id', 'tal_name')
    return JsonResponse({'taluka': list(talukas)})

def get_villages(request, taluka_id):
    villages = VillageHeaderAll.objects.filter(tal_id=taluka_id, status=True).values('vil_id', 'name')
    return JsonResponse({'village': list(villages)})

def search_states(request):
    query = request.GET.get('query', '')
    states = StateHeaderAll.objects.filter(
        Q(st_name__icontains=query) & Q(st_status=True)
    ).values('st_id', 'st_name', 'st_status')
    return JsonResponse({
        'states': list(states),
        'has_results': len(states) > 0
    })

def search_districts(request):
    query = request.GET.get('query', '')
    state_id = request.GET.get('state_id', '')
    districts = DistrictHeaderAll.objects.filter(
        Q(dist_name__icontains=query)
    )
    if state_id:
        districts = districts.filter(st_id=state_id)
    districts = districts.values('dist_id', 'dist_name', 'status', 'st_id__st_name')
    return JsonResponse({
        'districts': list(districts),
        'has_results': len(districts) > 0
    })

def search_talukas(request):
    query = request.GET.get('query', '')
    district_id = request.GET.get('district_id', '')
    talukas = TalukaHeaderAll.objects.filter(
        Q(tal_name__icontains=query)
    )
    if district_id:
        talukas = talukas.filter(dist_id=district_id)
    talukas = talukas.values('tal_id', 'tal_name', 'status', 'dist_id__dist_name', 'st_id__st_name')
    return JsonResponse({
        'talukas': list(talukas),
        'has_results': len(talukas) > 0
    })

def search_villages(request):
    query = request.GET.get('query', '')
    taluka_id = request.GET.get('taluka_id', '')
    villages = VillageHeaderAll.objects.filter(
        Q(name__icontains=query)
    )
    if taluka_id:
        villages = villages.filter(tal_id=taluka_id)
    villages = villages.values('vil_id', 'name', 'status', 'tal_id__tal_name', 'dist_id__dist_name', 'st_id__st_name')
    return JsonResponse({
        'villages': list(villages),
        'has_results': len(villages) > 0
    })

def add_district(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)
    
    district_name = request.POST.get('district_name')
    state_id = request.POST.get('state_id')
    if not district_name or not state_id:
        return JsonResponse({'status': 'error', 'message': 'District name and State ID are required'}, status=400)
    
    district_name = district_name.strip()
    if len(district_name) < 2:
        return JsonResponse({'status': 'error', 'message': 'District name must be at least 2 characters long'}, status=400)
    
    try:
        state = get_object_or_404(StateHeaderAll, st_id=state_id)
        district = DistrictHeaderAll.objects.create(
            st_id=state,
            dist_name=district_name,
            status=True
        )
        return JsonResponse({
            'status': 'success',
            'district': {
                'dist_id': district.dist_id,
                'dist_name': district.dist_name,
                'status': district.status,
                'st_id__st_name': district.st_id.st_name
            }
        })
    except IntegrityError:
        return JsonResponse({'status': 'error', 'message': 'A district with this name already exists in this state'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Failed to add district: {str(e)}'}, status=500)

def add_taluka(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)
    
    taluka_name = request.POST.get('taluka_name')
    district_id = request.POST.get('district_id')
    if not taluka_name or not district_id:
        return JsonResponse({'status': 'error', 'message': 'Taluka name and District ID are required'}, status=400)
    
    taluka_name = taluka_name.strip()
    if len(taluka_name) < 2:
        return JsonResponse({'status': 'error', 'message': 'Taluka name must be at least 2 characters long'}, status=400)
    
    try:
        district = get_object_or_404(DistrictHeaderAll, dist_id=district_id)
        taluka = TalukaHeaderAll.objects.create(
            st_id=district.st_id,
            dist_id=district,
            tal_name=taluka_name,
            status=True
        )
        return JsonResponse({
            'status': 'success',
            'taluka': {
                'tal_id': taluka.tal_id,
                'tal_name': taluka.tal_name,
                'status': taluka.status,
                'dist_id__dist_name': taluka.dist_id.dist_name,
                'st_id__st_name': taluka.st_id.st_name
            }
        })
    except IntegrityError:
        return JsonResponse({'status': 'error', 'message': 'A taluka with this name already exists in this district'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Failed to add taluka: {str(e)}'}, status=500)

def add_village(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)
    
    village_name = request.POST.get('village_name')
    taluka_id = request.POST.get('taluka_id')
    if not village_name or not taluka_id:
        return JsonResponse({'status': 'error', 'message': 'Village name and Taluka ID are required'}, status=400)
    
    village_name = village_name.strip()
    if len(village_name) < 2:
        return JsonResponse({'status': 'error', 'message': 'Village name must be at least 2 characters long'}, status=400)
    
    try:
        taluka = get_object_or_404(TalukaHeaderAll, tal_id=taluka_id)
        village = VillageHeaderAll.objects.create(
            st_id=taluka.st_id,
            dist_id=taluka.dist_id,
            tal_id=taluka,
            name=village_name,
            status=True
        )
        return JsonResponse({
            'status': 'success',
            'village': {
                'vil_id': village.vil_id,
                'name': village.name,
                'status': village.status,
                'tal_id__tal_name': village.tal_id.tal_name,
                'dist_id__dist_name': village.dist_id.dist_name,
                'st_id__st_name': village.st_id.st_name
            }
        })
    except IntegrityError:
        return JsonResponse({'status': 'error', 'message': 'A village with this name already exists in this taluka'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Failed to add village: {str(e)}'}, status=500)