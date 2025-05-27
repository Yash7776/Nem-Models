from django.db import models, transaction
from django.utils import timezone
from django.core.validators import RegexValidator
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.postgres.fields import ArrayField
import string

class Profile_header_all(models.Model):
    profile_id = models.CharField(max_length=20, unique=True)
    profile_name = models.CharField(max_length=100)
    pro_form_ids = ArrayField(models.CharField(), default=list, blank=True, help_text="List of accessible Form IDs like ['F_MAN_001', 'F_MAIN_002']")
    pro_process_ids = ArrayField(models.CharField(), default=list, blank=True, help_text="List of accessible Process IDs like ['P_MAN_0001', 'P_DOC_0002']")
    is_active = models.BooleanField(default=True) #profile_status

    def __str__(self):
        return f"{self.profile_id} - {self.profile_name}"

class UniqueIdHeaderAll(models.Model):
    table_name = models.CharField(max_length=100)
    id_for = models.CharField(max_length=50)
    prefix = models.CharField(max_length=20)
    last_id = models.CharField(max_length=15)
    created_on = models.DateTimeField()
    modified_on = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.created_on:
            self.created_on = timezone.now()
        self.modified_on = timezone.now()
        super().save(*args, **kwargs)

    def increment_alphanumeric(self, s):
        """
        Increment a 5-character alphanumeric string (00001 to ZZZZZ).
        """
        chars = string.digits + string.ascii_uppercase  # 0-9, then A-Z
        base = len(chars)  # 36 (10 digits + 26 letters)
        s = s.rjust(5, '0')  # Ensure length is 5, pad with leading zeros

        # Convert to number
        num = 0
        for c in s:
            num = num * base + chars.index(c)

        # Increment
        num += 1
        if num > base ** 5:  # If we exceed ZZZZZ
            raise ValueError("ID limit exceeded (ZZZZZ reached)")

        # Convert back to string
        new_s = ''
        for _ in range(5):
            new_s = chars[num % base] + new_s
            num //= base

        return new_s.rjust(5, '0'), num  # Return the new ID and its numeric position

    def get_next_id(self):
        if not self.last_id:
            self.last_id = f"{self.prefix}-00001"  # Start from "prefix-00001"
            sequence_number = 1
        else:
            # Extract the alphanumeric part from last_id (e.g., "00001" from "UHA-00001")
            current_id = self.last_id.split('-')[-1]
            # Increment the alphanumeric part
            next_id, sequence_number = self.increment_alphanumeric(current_id)
            # Store last_id with the prefix
            self.last_id = f"{self.prefix}-{next_id}"

        self.save()
        return self.last_id, sequence_number  # Return the formatted ID and sequence number

    def __str__(self):
        return f"{self.prefix}_{self.last_id} for {self.id_for} in {self.table_name}"

class User_header_all(models.Model):
    mobile_validator = RegexValidator(
        regex=r'^[6-9]\d{9}$',
        message='Mobile number must be 10 digits and start with 6, 7, 8, or 9.'
    )

    user_id = models.IntegerField()
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

    def _str_(self):
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
            id_for='user',
            defaults={
                'last_id': '',
                'created_on': timezone.now(),
                'modified_on': timezone.now()
            }
        )
        _, sequence_number = unique_id.get_next_id()  # Get the sequence number
        return sequence_number

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


