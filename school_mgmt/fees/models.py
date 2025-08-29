from django.db import models

# Create your models here.
class Fee(models.Model):
    student = models.ForeignKey("students.Student", on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    status = models.CharField(max_length=10, choices=[("Paid", "Paid"), ("Unpaid", "Unpaid")])
    due_date = models.DateField()

    def __str__(self):
        return f"{self.student} - {self.amount} - {self.status}"
    