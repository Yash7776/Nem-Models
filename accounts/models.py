from django.db import models, transaction
from django.utils import timezone
from django.core.validators import RegexValidator
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.postgres.fields import ArrayField
import re

class Profile_header_all(models.Model):
    profile_id = models.CharField(max_length=20, unique=True)
    profile_name = models.CharField(max_length=100)
    pro_form_ids = ArrayField(models.CharField(), default=list, blank=True, help_text="List of accessible Form IDs like ['F_MAN_001', 'F_MAIN_002']")
    pro_process_ids = ArrayField(models.CharField(), default=list, blank=True, help_text="List of accessible Process IDs like ['P_MAN_0001', 'P_DOC_0002']")
    p_status = models.BooleanField(default=True)  # Renamed from is_active
    pro_inserted_on = models.DateTimeField(auto_now_add=True)  # New field for creation time
    pro_deactivated_on = models.DateTimeField(null=True, blank=True)  # New field for deactivation time

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
        # Set pro_deactivated_on when p_status is False
        if not self.p_status and not self.pro_deactivated_on:
            self.pro_deactivated_on = timezone.now()
        elif self.p_status and self.pro_deactivated_on:
            # Clear pro_deactivated_on if p_status is True
            self.pro_deactivated_on = None
        super().save(*args, **kwargs)

class UniqueIdHeaderAll(models.Model):
    table_name = models.CharField(max_length=100)
    id_for = models.CharField(max_length=50)
    prefix = models.CharField(max_length=3)  # E.g., UHA, PHA
    last_id = models.CharField(max_length=15)  # E.g., PHA-A0001
    created_on = models.DateTimeField()
    modified_on = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.created_on:
            self.created_on = timezone.now()
        self.modified_on = timezone.now()
        super().save(*args, **kwargs)

    def get_next_id(self):
        if not self.last_id:
            # Initialize with the first ID, e.g., PHA-A0001
            next_id = f"{self.prefix}-A0001"
            self.last_id = next_id
            self.save()
            return next_id

        # Parse the last_id, e.g., PHA-A0001 -> prefix: PHA, alphabets: A, digits: 0001
        last_id_parts = self.last_id.split('-')
        if len(last_id_parts) != 2:
            raise ValueError(f"Invalid last_id format: {self.last_id}")

        prefix, rest = last_id_parts
        alphabets = ''.join(re.findall(r'[A-Z]', rest))
        digits = ''.join(re.findall(r'\d+', rest))

        # Total length of alphabets + digits must be 5
        alpha_len = len(alphabets)
        digit_len = 5 - alpha_len  # Number of digits decreases as alphabets increase

        if alpha_len == 5:
            raise ValueError("Reached the maximum ID limit: ZZZZZ")

        # Check if we need to increment the alphabetic part
        if digits == '9' * digit_len:  # e.g., 9999, 999, 99, 9
            if alphabets == 'Z' and alpha_len == 1:
                alphabets = 'ZA'  # Z -> ZA
                digits = '001'    # 3 digits (ZA001)
            elif alphabets == 'ZZ' and alpha_len == 2:
                alphabets = 'ZZA'  # ZZ -> ZZA
                digits = '01'      # 2 digits (ZZA01)
            elif alphabets == 'ZZZ' and alpha_len == 3:
                alphabets = 'ZZZZ'  # ZZZ -> ZZZZ
                digits = '1'        # 1 digit (ZZZZ1)
            elif alphabets == 'ZZZZ' and alpha_len == 4:
                alphabets = 'ZZZZZ'  # ZZZZ -> ZZZZZ
                digits = ''          # 0 digits (ZZZZZ)
            elif alpha_len == 0:
                alphabets = 'A'      # 9999 -> A0001
                digits = '0001'      # 4 digits (A0001)
            elif alpha_len in [1, 2, 3] and alphabets[-1] != 'Z':
                # A -> B, ZA -> ZB, ZZA -> ZZB
                last_char = alphabets[-1]
                alphabets = alphabets[:-1] + chr(ord(last_char) + 1)
                digits = '1'.zfill(digit_len)  # Reset digits (e.g., 0001, 001, 01)
            elif alpha_len in [2, 3] and alphabets[-1] == 'Z':
                # ZA -> ZZA, ZZA -> ZZZA
                alphabets += 'A'
                digits = '1'.zfill(digit_len - 1)  # One less digit (e.g., 001, 01)
        else:
            # Increment the numeric part
            next_number = int(digits) + 1
            digits = str(next_number).zfill(digit_len)

        # Construct the next ID
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

    user_id = models.CharField(max_length=15)  # Supports format like UHA-A0001
    line_no = models.IntegerField(default=0)
    name = models.CharField(max_length=150)
    email = models.CharField(max_length=150, blank=True)
    username = models.CharField(max_length=150)
    password = models.CharField(max_length=128)
    designation = models.CharField(max_length=100)
    mobile_no = models.CharField(max_length=10, blank=True, validators=[mobile_validator])
    profile = models.ForeignKey(
        Profile_header_all,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='user_assignments'
    )
    is_active = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user_id', 'line_no')

    def __str__(self):
        return f"{self.username} (Line {self.line_no})"

    def save(self, *args, **kwargs):
        # Hash the password if it hasn't been hashed already
        if self.password and not self.password.startswith('pbkdf2_'):
            self.password = make_password(self.password)
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
        
        if User_header_all.objects.filter(user_id=self.user_id, profile=profile).exists():
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
                name=self.name,
                email=self.email,
                username=self.username,
                password=self.password,  # Password is already hashed
                designation=self.designation,
                mobile_no=self.mobile_no,
                profile=profile,
                is_active=True
            )

    def set_profile_active(self, line_no, active=True):
        assignment = User_header_all.objects.filter(user_id=self.user_id, line_no=line_no).first()
        if not assignment:
            raise ValueError(f"No profile found with line number {line_no}")
        assignment.is_active = active
        assignment.save()
        return assignment

    def get_active_profiles(self):
        assignments = User_header_all.objects.filter(user_id=self.user_id, is_active=True, profile__isnull=False)
        return [assignment.profile for assignment in assignments]

    def reset_profile_line_no(self):
        User_header_all.objects.filter(user_id=self.user_id).exclude(line_no=0).delete()
        default_assignment, _ = User_header_all.objects.get_or_create(
            user_id=self.user_id,
            line_no=0,
            defaults={
                'name': self.name,
                'email': self.email,
                'username': self.username,
                'password': self.password,  # Password is already hashed
                'designation': self.designation,
                'mobile_no': self.mobile_no,
                'profile': None,
                'is_active': True
            }
        )
        if default_assignment.profile:
            default_assignment.profile = None
            default_assignment.is_active = True
            default_assignment.save()