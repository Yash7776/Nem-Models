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
    name = models.CharField(max_length=150)
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=128)
    designation = models.CharField(max_length=100)
    mobile_no = models.CharField(max_length=15, unique=True)

    profiles = models.ManyToManyField(
        Profile_header_all,
        through='UserProfileAssignment',
        blank=True,
        related_name='users'
    )

    def __str__(self):
        return self.username

    def assign_profile(self, profile):
        from django.db.models import Max
        max_line = self.profile_assignments.aggregate(Max('line_no'))['line_no__max'] or 0
        return UserProfileAssignment.objects.create(
            user=self,
            profile=profile,
            line_no=max_line + 1,
            is_active=True
        )

    def set_profile_active(self, line_no, active=True):
        assignment = self.profile_assignments.get(line_no=line_no)
        assignment.is_active = active
        assignment.save()
        return assignment

    def get_active_profiles(self):
        return Profile_header_all.objects.filter(
            users=self,
            userprofileassignment__is_active=True
        )

    def reset_profile_line_no(self):
        """Reset profile assignments to default state (no profiles assigned)."""
        self.profile_assignments.all().delete()

class UserProfileAssignment(models.Model):
    user = models.ForeignKey(
        User_header_all,
        on_delete=models.CASCADE,
        related_name='profile_assignments'
    )
    profile = models.ForeignKey(Profile_header_all, on_delete=models.CASCADE)
    line_no = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = (('user', 'line_no'), ('user', 'profile'))
        ordering = ['line_no']

    def __str__(self):
        status = 'active' if self.is_active else 'inactive'
        return f"{self.user.username} slot #{self.line_no} → {self.profile.profile_id} ({status})"