from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser, Admin
from students.models import Student, Guardian
from teachers.models import Teacher
import uuid  # For auto-generating employee_id if needed

@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.role == 'student':
            Student.objects.create(
                user=instance,
                admission_number=instance.admission_number or f"STD-{uuid.uuid4().hex[:6].upper()}"
            )
            instance.admission_number = None

        elif instance.role == 'teacher':
            # Auto-generate employee_id if not provided
            Teacher.objects.create(
                user=instance,
                employee_id=instance.employee_id or f"TCH-{uuid.uuid4().hex[:6].upper()}"
            )
            instance.employee_id = None

        elif instance.role == 'guardian':
            Guardian.objects.create(
                user=instance
            )
            instance.occupation = None

        elif instance.role == 'admin':
            Admin.objects.create(
                user=instance,
                employee_id=instance.employee_id or f"ADM-{uuid.uuid4().hex[:6].upper()}",
                department=instance.department or "General"
            )
            instance.employee_id = None
            instance.department = None

        instance.save()