from django.db import models

# Create your models here.
class Attendance(models.Model):
    student = models.ForeignKey("students.Student", on_delete=models.CASCADE)
    date = models.DateTimeField()
    status = models.CharField(max_length=10, choices=[("Present", "Present"), ("Absent", "Absent")])

    def __str__(self):
        return f"{self.student} - {self.date} - {self.status}"
    