from django.db import models
from accounts.models import CustomUser
from academics.utils import current_academic_year
from academics.models import ClassTeaching, Subject, Class


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
    
    # Add subjects relationship through TeacherSubjectAssignment
    subjects = models.ManyToManyField(
        'academics.Subject',
        through='TeacherSubjectAssignment',
        related_name='teachers',
        blank=True
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
        year_var = current_year.split('-')[0] if '-' in current_year else current_year
        
        # Use ClassTeaching model to get classroom assignments
        return ClassTeaching.objects.filter(
            teacher=self,
            subjects__academic_year=year_var  # Filter by subject's academic year
        ).select_related('classroom').prefetch_related('subjects').distinct()
    
    def get_current_subjects(self):
        """Get subjects currently being taught by this teacher using the new relationship"""
        current_year = current_academic_year()
        year_var = current_year.split('-')[0] if '-' in current_year else current_year
        
        # Use the new TeacherSubjectAssignment relationship
        return Subject.objects.filter(
            teacher_assignments__teacher=self,  # Through TeacherSubjectAssignment
            teacher_assignments__academic_year=year_var
        ).distinct()

    def get_current_classes(self):
        """Get classes currently assigned to this teacher"""
        current_year = current_academic_year()
        year_var = current_year.split('-')[0] if '-' in current_year else current_year
        
        # Use ClassTeaching model
        return Class.objects.filter(
            teaching_assignments__teacher=self,
            teaching_assignments__subjects__academic_year=year_var
        ).distinct()

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


class TeacherSubjectAssignment(models.Model):
    teacher = models.ForeignKey("Teacher", on_delete=models.CASCADE, related_name='subject_assignments')
    subject = models.ForeignKey("academics.Subject", on_delete=models.CASCADE, related_name='teacher_assignments')
    academic_year = models.CharField(max_length=9, default=current_academic_year)
    date_assigned = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ('teacher', 'subject', 'academic_year')
        verbose_name = "Teacher Subject Assignment"
        verbose_name_plural = "Teacher Subject Assignments"

    def __str__(self):
        return f"{self.teacher} - {self.subject} ({self.academic_year})"