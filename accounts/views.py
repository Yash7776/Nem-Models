from django.shortcuts import render, get_object_or_404, redirect
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
    profile_id = request.GET.get('profile_id')  # Get profile_id from query parameters
    if not profile_id:
        return redirect('accounts:user_detail', username=username)  # Redirect if no profile_id
    profile = get_object_or_404(Profile_header_all, profile_id=profile_id)
    user.assign_profile(profile)
    return redirect('accounts:user_detail', username=username)

def toggle_profile_status(request, username, line_no):
    user = get_object_or_404(User_header_all, username=username, line_no=0)
    is_active = request.GET.get('is_active', 'true').lower() == 'true'
    user.set_profile_active(line_no, is_active)
    return redirect('accounts:user_detail', username=username)

def all_users(request):
    rows = User_header_all.objects.all().order_by('id')
    return render(request, 'accounts/all_users.html', {'rows': rows})

def create_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        name = request.POST.get('name')
        email = request.POST.get('email', '')
        password = request.POST.get('password')
        designation = request.POST.get('designation')
        mobile_no = request.POST.get('mobile_no', '')

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
        return redirect('accounts:user_detail', username=username)
    return render(request, 'accounts/create_user.html')