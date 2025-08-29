from django.db import models
from accounts.models import CustomUser
from academics.utils import current_academic_year
from academics.models import ClassTeaching

class Teacher(models.Model):
    user = models.OneToOneField(
        CustomUser, 
        on_delete=models.CASCADE,
        related_name='teacher_profile'
    )
    employee_id = models.CharField(max_length=20, unique=True)
    specialization = models.CharField(max_length=100)
    qualification = models.CharField(max_length=100, blank=True)
    joining_date = models.DateTimeField(auto_now_add=True)
    is_class_teacher = models.BooleanField(default=False)
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(
        upload_to='teachers/profiles/',
        blank=True,
        null=True
    )

    class Meta:
        ordering = ['user__last_name', 'user__first_name']
        verbose_name = "Teacher"
        verbose_name_plural = "Teachers"

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.employee_id})"

    def currently_teaching(self):
        """Get classes and subjects currently being taught by this teacher"""
        current_year = current_academic_year()
        # Get through ClassTeaching with subjects filtered by academic year
        return ClassTeaching.objects.filter(
            teacher=self,
            subjects__academic_year=current_year
        ).select_related('classroom', 'teacher').prefetch_related('subjects').distinct()
        
    @property
    def email(self):
        return self.user.email

    @property
    def first_name(self):
        return self.user.first_name

    @property
    def last_name(self):
        return self.user.last_name

    @property
    def full_name(self):
        return self.user.get_full_name()