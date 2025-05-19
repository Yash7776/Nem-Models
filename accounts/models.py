from django.db import models

class Profile_header_all(models.Model):
    profile_id = models.CharField(max_length=20, unique=True)
    profile_name = models.CharField(max_length=100)
    pro_form_ids = models.JSONField(default=list, blank=True)
    pro_process_ids = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.profile_id} - {self.profile_name}"

class User_header_all(models.Model):
    user_id = models.IntegerField()  # To group user entries
    line_no = models.IntegerField(default=0)  # To indicate the assignment slot
    name = models.CharField(max_length=150)
    email = models.CharField(max_length=150, blank=True)
    username = models.CharField(max_length=150)
    password = models.CharField(max_length=128)
    designation = models.CharField(max_length=100)
    mobile_no = models.CharField(max_length=15, blank=True)
    profile = models.ForeignKey(
        Profile_header_all,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='user_assignments'
    )

    class Meta:
        unique_together = ('user_id', 'line_no')  # Ensure unique line_no per user

    def __str__(self):
        return f"{self.username} (Line {self.line_no})"

    def assign_profile(self, profile):
        """Assign a profile to the user with the next available line number."""
        if not isinstance(profile, Profile_header_all):
            raise ValueError("Invalid profile instance")
        
        # Check if the profile is already assigned to this user
        if User_header_all.objects.filter(user_id=self.user_id, profile=profile).exists():
            return

        # Get the next line number for this user
        max_line = User_header_all.objects.filter(user_id=self.user_id).aggregate(
            models.Max('line_no')
        )['line_no__max'] or -1
        next_line_no = max_line + 1

        # Create a new User_header_all instance for this assignment
        User_header_all.objects.create(
            user_id=self.user_id,
            line_no=next_line_no,
            name=self.name,
            email=self.email,
            username=self.username,
            password=self.password,
            designation=self.designation,
            mobile_no=self.mobile_no,
            profile=profile
        )

    def set_profile_active(self, line_no, active=True):
        """Activate or deactivate a profile at the specified line number."""
        assignment = User_header_all.objects.filter(user_id=self.user_id, line_no=line_no).first()
        if not assignment:
            raise ValueError(f"No profile found with line number {line_no}")
        # Simulate active/inactive by setting profile to None if inactive
        if active and assignment.profile is None:
            # You might need to reassign a profile here; for now, raise an error
            raise ValueError("Cannot activate without a profile. Reassign a profile first.")
        elif not active:
            assignment.profile = None
            assignment.save()
        return assignment

    def get_active_profiles(self):
        """Return a list of active Profile_header_all instances for this user."""
        assignments = User_header_all.objects.filter(user_id=self.user_id, profile__isnull=False)
        return [assignment.profile for assignment in assignments]

    def reset_profile_line_no(self):
        """Reset profile assignments to default state (line_no=0)."""
        # Delete all assignments for this user except line_no=0
        User_header_all.objects.filter(user_id=self.user_id).exclude(line_no=0).delete()
        # Ensure line_no=0 exists with no profile
        default_assignment, _ = User_header_all.objects.get_or_create(
            user_id=self.user_id,
            line_no=0,
            defaults={
                'name': self.name,
                'email': self.email,
                'username': self.username,
                'password': self.password,
                'designation': self.designation,
                'mobile_no': self.mobile_no,
                'profile': None
            }
        )
        if default_assignment.profile:
            default_assignment.profile = None
            default_assignment.save()