from django.db import models, transaction
from django.utils import timezone
from django.core.validators import RegexValidator
from django.contrib.auth.hashers import make_password
from django.contrib.postgres.fields import ArrayField
import re

class StateHeaderAll(models.Model):
    st_id = models.AutoField(primary_key=True)
    st_name = models.CharField(max_length=100)
    st_inserted_on = models.DateTimeField(auto_now_add=True)
    st_status = models.BooleanField(default=True)

    def __str__(self):
        return self.st_name

class DistrictHeaderAll(models.Model):
    dist_id = models.AutoField(primary_key=True)
    st_id = models.ForeignKey(StateHeaderAll, on_delete=models.CASCADE)
    dist_name = models.CharField(max_length=100)
    inserted = models.DateTimeField(auto_now_add=True)
    status = models.BooleanField(default=True)

    def __str__(self):
        return self.dist_name

class TalukaHeaderAll(models.Model):
    tal_id = models.AutoField(primary_key=True)
    dist_id = models.ForeignKey(DistrictHeaderAll, on_delete=models.CASCADE)
    st_id = models.ForeignKey(StateHeaderAll, on_delete=models.CASCADE)
    tal_name = models.CharField(max_length=100)
    inserted = models.DateTimeField(auto_now_add=True)
    status = models.BooleanField(default=True)

    def __str__(self):
        return self.tal_name

class VillageHeaderAll(models.Model):
    vil_id = models.AutoField(primary_key=True)
    tal_id = models.ForeignKey(TalukaHeaderAll, on_delete=models.CASCADE)
    dist_id = models.ForeignKey(DistrictHeaderAll, on_delete=models.CASCADE)
    st_id = models.ForeignKey(StateHeaderAll, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    inserted = models.DateTimeField(auto_now_add=True)
    status = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class ProjectLocationDetailsAll(models.Model):
    LOCATION_TYPE_CHOICES = (
        (1, 'State'),
        (2, 'District'),
        (3, 'Taluka'),
        (4, 'Village'),
    )

    pl_id = models.AutoField(primary_key=True)
    project_id = models.ForeignKey('Project',on_delete=models.SET_NULL,null=True,blank=True,related_name='project_assighment'
    )
    pl_location_type = models.IntegerField(choices=LOCATION_TYPE_CHOICES)

    st_id = models.ForeignKey(StateHeaderAll, on_delete=models.CASCADE, null=True, blank=True)
    dist_id = models.ForeignKey(DistrictHeaderAll, on_delete=models.CASCADE, null=True, blank=True)
    tal_id = models.ForeignKey(TalukaHeaderAll, on_delete=models.CASCADE, null=True, blank=True)
    vil_id = models.ForeignKey(VillageHeaderAll, on_delete=models.CASCADE, null=True, blank=True)

    inserted = models.DateTimeField(auto_now_add=True)
    status = models.BooleanField(default=True)

    def __str__(self):
        return f"Project {self.project_id} - Type {self.get_pl_location_type_display()}"

class Department(models.Model):
    dept_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.dept_id

class Project(models.Model):
    # Choices for Yes/No dropdown
    YES_NO_CHOICES = [
        ('Yes', 'Yes'),
        ('No', 'No'),
    ]

    project_id = models.CharField(max_length=20, unique=True, blank=True)  # Changed from AutoField
    project_name = models.CharField(max_length=100)
    project_description = models.TextField(blank=True)
    display_order = models.IntegerField(default=0)
    project_details_KM = models.CharField(max_length=100)
    project_status = models.IntegerField(choices=[(0, 'Suspend'), (1, 'Active')], default=1)
    project_type = models.CharField(max_length=100)
    project_admin_name = models.CharField(max_length=100)
    Project_reg_contractors = models.PositiveIntegerField(default=0)
    project_admins_users = models.PositiveIntegerField(default=0)
    from_KM = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    to_KM = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, null=True, blank=True, related_name='projects')
    step_statuses = models.JSONField(default=dict, blank=True)
    survey_properties = models.CharField(max_length=3, choices=YES_NO_CHOICES, default='Yes')
    field_survey = models.CharField(max_length=3, choices=YES_NO_CHOICES, default='No')

    class Meta:
        ordering = ['display_order', 'project_name']

    def __str__(self):
        return f"{self.project_id} - {self.project_name}"

    def save(self, *args, **kwargs):
        if not self.project_id:
            unique_id, _ = UniqueIdHeaderAll.objects.get_or_create(
                table_name='project',
                id_for='project_id',
                defaults={
                    'prefix': 'PRO',
                    'last_id': '',
                    'created_on': timezone.now(),
                    'modified_on': timezone.now()
                }
            )
            self.project_id = unique_id.get_next_id()
        super().save(*args, **kwargs)

    @classmethod
    def get_or_assign_project_id(cls, project_name):
        existing_project = cls.objects.filter(project_name=project_name).first()
        if existing_project:
            return existing_project.project_id
        unique_id, _ = UniqueIdHeaderAll.objects.get_or_create(
            table_name='project',
            id_for='project_id',
            defaults={
                'prefix': 'PRO',
                'last_id': '',
                'created_on': timezone.now(),
                'modified_on': timezone.now()
            }
        )
        return unique_id.get_next_id()

class Profile_header_all(models.Model):
    profile_id = models.CharField(max_length=20, unique=True,blank=True,null=True)
    profile_name = models.CharField(max_length=100)
    pro_form_ids = ArrayField(models.CharField(), default=list, blank=True, help_text="List of accessible Form IDs like ['F_MAN_001', 'F_MAIN_002']")
    pro_process_ids = ArrayField(models.CharField(), default=list, blank=True, help_text="List of accessible Process IDs like ['P_MAN_0001', 'P_DOC_0002']")
    p_status = models.BooleanField(default=True)
    pro_inserted_on = models.DateTimeField(auto_now_add=True)
    pro_deactivated_on = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.profile_id} - {self.profile_name}"

    @classmethod
    def get_or_assign_profile_id(cls, profile_name):
        existing_profile = cls.objects.filter(profile_name=profile_name).first()
        if existing_profile:
            return existing_profile.profile_id
        unique_id, _ = UniqueIdHeaderAll.objects.get_or_create(
            table_name='profile_header_all',
            id_for='profile_id',
            defaults={
                'prefix': 'PHA',
                'last_id': '',
                'created_on': timezone.now(),
                'modified_on': timezone.now()
            }
        )
        return unique_id.get_next_id()

    def save(self, *args, **kwargs):
        if not self.profile_id:
            self.profile_id = self.get_or_assign_profile_id(self.profile_name)
        if not self.p_status and not self.pro_deactivated_on:
            self.pro_deactivated_on = timezone.now()
        elif self.p_status and self.pro_deactivated_on:
            self.pro_deactivated_on = None
        super().save(*args, **kwargs)

class UniqueIdHeaderAll(models.Model):
    table_name = models.CharField(max_length=100)
    id_for = models.CharField(max_length=50)
    prefix = models.CharField(max_length=3)
    last_id = models.CharField(max_length=15)
    created_on = models.DateTimeField()
    modified_on = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.created_on:
            self.created_on = timezone.now()
        self.modified_on = timezone.now()
        super().save(*args, **kwargs)

    def get_next_id(self):
        if not self.last_id:
            next_id = f"{self.prefix}-A0001"
            self.last_id = next_id
            self.save()
            return next_id
        last_id_parts = self.last_id.split('-')
        if len(last_id_parts) != 2:
            raise ValueError(f"Invalid last_id format: {self.last_id}")
        prefix, rest = last_id_parts
        alphabets = ''.join(re.findall(r'[A-Z]', rest))
        digits = ''.join(re.findall(r'\d+', rest))
        alpha_len = len(alphabets)
        digit_len = 5 - alpha_len
        if alpha_len == 5:
            raise ValueError("Reached the maximum ID limit: ZZZZZ")
        if digits == '9' * digit_len:
            if alphabets == 'Z' and alpha_len == 1:
                alphabets = 'ZA'
                digits = '001'
            elif alphabets == 'ZZ' and alpha_len == 2:
                alphabets = 'ZZA'
                digits = '01'
            elif alphabets == 'ZZZ' and alpha_len == 3:
                alphabets = 'ZZZZ'
                digits = '1'
            elif alphabets == 'ZZZZ' and alpha_len == 4:
                alphabets = 'ZZZZZ'
                digits = ''
            elif alpha_len == 0:
                alphabets = 'A'
                digits = '0001'
            elif alpha_len in [1, 2, 3] and alphabets[-1] != 'Z':
                last_char = alphabets[-1]
                alphabets = alphabets[:-1] + chr(ord(last_char) + 1)
                digits = '1'.zfill(digit_len)
            elif alpha_len in [2, 3] and alphabets[-1] == 'Z':
                alphabets += 'A'
                digits = '1'.zfill(digit_len - 1)
        else:
            next_number = int(digits) + 1
            digits = str(next_number).zfill(digit_len)
        next_id = f"{self.prefix}-{alphabets}{digits}"
        self.last_id = next_id
        self.save()
        return next_id

    def __str__(self):
        return f"{self.table_name}"

class User_header_all(models.Model):
    mobile_validator = RegexValidator(
        regex=r'^[6-9]\d{9}$',
        message='Mobile number must be 10 digits and start with 6, 7, 8, or 9.'
    )
    STATUS_CHOICES = (
        (1, 'Active'),
        (0, 'Inactive'),
    )
    USER_TYPE_CHOICES = (
        (1, 'Platform owner'),
        (2, 'Department'),
        (3, 'Contractor'),
    )

    user_id = models.CharField(max_length=15)
    line_no = models.IntegerField(default=0)
    full_name = models.CharField(max_length=150)
    email = models.CharField(max_length=150, blank=True)
    username = models.CharField(max_length=150)
    password = models.CharField(max_length=128)
    mobile_no = models.CharField(max_length=10, blank=True, validators=[mobile_validator])
    profile_id = models.ForeignKey(
        'Profile_header_all',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='user_assignments'
    )
    project_id = models.JSONField(default=dict)
    user_type = models.IntegerField(choices=USER_TYPE_CHOICES, default=1)
    status = models.IntegerField(choices=STATUS_CHOICES, default=1)
    inserted_on = models.DateTimeField(auto_now_add=True)
    deactivated_on = models.DateTimeField(null=True, blank=True)
    st_id = models.ForeignKey(StateHeaderAll, on_delete=models.SET_NULL, null=True, blank=True)
    dist_id = models.ForeignKey(DistrictHeaderAll, on_delete=models.SET_NULL, null=True, blank=True)
    tal_id = models.ForeignKey(TalukaHeaderAll, on_delete=models.SET_NULL, null=True, blank=True)
    vil_id = models.ForeignKey(VillageHeaderAll, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = ('user_id', 'line_no')

    def __str__(self):
        return f"{self.username} (Line {self.line_no})"

    def save(self, *args, **kwargs):
        if self.password and not self.password.startswith('pbkdf2_'):
            self.password = make_password(self.password)
        if self.status == 0 and not self.deactivated_on:
            self.deactivated_on = timezone.now()
        elif self.status == 1 and self.deactivated_on:
            self.deactivated_on = None
        super().save(*args, **kwargs)

    @classmethod
    def get_or_assign_user_id(cls, username):
        existing_user = cls.objects.filter(username=username).first()
        if existing_user:
            return existing_user.user_id
        unique_id, _ = UniqueIdHeaderAll.objects.get_or_create(
            table_name='user_header_all',
            id_for='user_id',
            defaults={
                'prefix': 'UHA',
                'last_id': '',
                'created_on': timezone.now(),
                'modified_on': timezone.now()
            }
        )
        return unique_id.get_next_id()

    def assign_profile(self, profile):
        if not isinstance(profile, Profile_header_all):
            raise ValueError("Invalid profile instance")
        if User_header_all.objects.filter(user_id=self.user_id, profile_id=profile).exists():
            return
        with transaction.atomic():
            max_line = User_header_all.objects.filter(user_id=self.user_id).select_for_update().aggregate(
                models.Max('line_no')
            )['line_no__max']
            if max_line is None:
                max_line = -1
            next_line_no = max_line + 1
            User_header_all.objects.create(
                user_id=self.user_id,
                line_no=next_line_no,
                full_name=self.full_name,
                email=self.email,
                username=self.username,
                password=self.password,
                mobile_no=self.mobile_no,
                profile_id=profile,
                project_id=self.project_id,
                user_type=self.user_type,
                status=1,
                inserted_on=timezone.now(),
                deactivated_on=None,
                st_id=self.st_id,
                dist_id=self.dist_id,
                tal_id=self.tal_id,
                vil_id=self.vil_id
            )

    def set_profile_active(self, line_no, active=True):
        assignment = User_header_all.objects.filter(user_id=self.user_id, line_no=line_no).first()
        if not assignment:
            raise ValueError(f"No profile found with line number {line_no}")
        assignment.status = 1 if active else 0
        assignment.save()
        return assignment

    def get_active_profiles(self):
        assignments = User_header_all.objects.filter(user_id=self.user_id, status=1, profile_id__isnull=False)
        return [assignment.profile_id for assignment in assignments]

    def reset_profile_line_no(self):
        User_header_all.objects.filter(user_id=self.user_id).exclude(line_no=0).delete()
        default_assignment, _ = User_header_all.objects.get_or_create(
            user_id=self.user_id,
            line_no=0,
            defaults={
                'full_name': self.full_name,
                'email': self.email,
                'username': self.username,
                'password': self.password,
                'mobile_no': self.mobile_no,
                'profile_id': None,
                'project_id': self.project_id,
                'user_type': self.user_type,
                'status': 1,
                'inserted_on': timezone.now(),
                'deactivated_on': None,
                'st_id': self.st_id,
                'dist_id': self.dist_id,
                'tal_id': self.tal_id,
                'vil_id': self.vil_id
            }
        )
        if default_assignment.profile_id:
            default_assignment.profile_id = None
            default_assignment.status = 1
            default_assignment.deactivated_on = None
            default_assignment.save()

    def get_projects_for_department(self, dept_id):
        projects = Project.objects.filter(department__dept_id=dept_id).values_list('project_id', flat=True)
        return list(projects)

    def assign_projects_to_department(self, dept_id, project_ids):
        if not self.project_id:
            self.project_id = {}
        valid_project_ids = self.get_projects_for_department(dept_id)
        invalid_projects = [pid for pid in project_ids if pid not in valid_project_ids]
        if invalid_projects:
            raise ValueError(f"Projects {invalid_projects} do not belong to department {dept_id}")
        self.project_id[dept_id] = project_ids
        self.save()