from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ("admin", "Admin"),
        ("student", "Student"),
        ("teacher", "Teacher"),
        ("guardian", "Guardian")
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    
    # Temporary registration fields
    admission_number = models.CharField(max_length=20, blank=True, null=True)
    employee_id = models.CharField(max_length=20, blank=True, null=True)
    occupation = models.CharField(max_length=100, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.role})" if self.get_full_name() else f"{self.username} ({self.role})"

    def is_student(self):
        return self.role == "student"
    
    def is_teacher(self):
        return self.role == "teacher"
    
    def is_guardian(self):
        return self.role == "guardian"
    
    def is_admin(self):
        return self.role == "admin" or self.is_superuser

    @property
    def student_profile(self):
        if hasattr(self, 'student'):
            return self.student
        return None
    
    @property
    def teacher_profile(self):
        if hasattr(self, 'teacher'):
            return self.teacher
        return None
    
    @property
    def guardian_profile(self):
        if hasattr(self, 'guardian'):
            return self.guardian
        return None

class Admin(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    employee_id = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=100)
    
    def __str__(self):
        return f"{self.user.email} (Admin)"