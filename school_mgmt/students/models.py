from django.db import models
from accounts.models import CustomUser
from django.core.validators import RegexValidator
from datetime import date
from django.utils import timezone

# Create your models here.
class Guardian(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    address = models.TextField(blank=True)
    relationship_to_student = models.CharField(max_length=50, blank=True)

    @property
    def students(self):
        """Get all students associated with this guardian"""
        return self.ward_students.all()
    
    def __str__(self):
        return self.user.get_full_name()
    

class Student(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, primary_key=True)
    admission_number = models.CharField(max_length=50, unique=True)
    date_of_birth = models.DateField(null=True, blank=True)
    current_class = models.ForeignKey("academics.Class", on_delete=models.SET_NULL, null=True, blank=True)
    guardian = models.ForeignKey(Guardian, on_delete=models.SET_NULL, null=True, blank=True, related_name='ward_students')

    def __str__(self):
        return self.user.get_full_name()

    class Meta:
        ordering = ["user__last_name"]
        verbose_name = "Student"
        verbose_name_plural = "Students"

    def age(self):
        """Calculate student's age"""
        if not self.date_of_birth:
            return None
        today = date.today()
        return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))

    def get_gpa(self):
        """Calculate student's GPA from all grades"""
        from academics.models import Grade
        grades = Grade.objects.filter(student=self)
        if grades.exists():
            return round(sum(g.marks for g in grades) / grades.count(), 2)
        return None

    @property
    def attendance_percentage(self):
        """Calculate attendance percentage for current month"""
        from attendance.models import Attendance
        current_month = timezone.now().month
        current_year = timezone.now().year
        
        total_days = Attendance.objects.filter(
            student=self,
            date__month=current_month,
            date__year=current_year
        ).count()
        
        if total_days == 0:
            return 0
            
        present_days = Attendance.objects.filter(
            student=self,
            status="Present",
            date__month=current_month,
            date__year=current_year
        ).count()
        
        return round((present_days / total_days) * 100, 2)