from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from academics.utils import current_academic_year

class Class(models.Model):
    name = models.CharField(max_length=20, unique=True)
    teachers = models.ManyToManyField(
        "teachers.Teacher",
        through='ClassTeaching',
        through_fields=('classroom', 'teacher'),
        related_name="classes"
    )

    def __str__(self):
        return self.name

    @property
    def student_count(self):
        """Count of students in this class"""
        return self.student_set.count()
    
    def get_primary_teacher(self):
        return self.teaching_assignments.filter(is_primary=True).first()

    def get_subjects(self):
        subjects = []
        seen = set()
        for assignment in self.teaching_assignments.all():
            for subject in assignment.subjects.all():
                if subject.id not in seen:
                    subjects.append(subject)
                    seen.add(subject.id)
        return subjects

    class Meta:
        verbose_name = "Class"
        verbose_name_plural = "Classes"
        ordering = ['name']

class ClassTeaching(models.Model):
    classroom = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='teaching_assignments')
    teacher = models.ForeignKey("teachers.Teacher", on_delete=models.CASCADE, related_name='class_assignments')
    is_primary = models.BooleanField(default=False)
    date_assigned = models.DateField(auto_now_add=True)
    subjects = models.ManyToManyField("Subject", blank=True)  # This can remain as M2M

    class Meta:
        unique_together = ('classroom', 'teacher')
        verbose_name = "Class Teaching Assignment"
        verbose_name_plural = "Class Teaching Assignments"

    def __str__(self):
        return f"{self.teacher} -> {self.classroom} (Primary: {self.is_primary})"

class Subject(models.Model):
    name = models.CharField(max_length=100)
    class_assigned = models.ForeignKey(
        Class, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='subjects'
    )
    teacher = models.ForeignKey(
        "teachers.Teacher",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    term = models.CharField(max_length=50, blank=True)
    academic_year = models.CharField(max_length=20)

    def __str__(self):
        return self.name

    def get_assigned_classes(self):
        return Class.objects.filter(
            teaching_assignments__subjects=self
        ).distinct()

    class Meta:
        ordering = ['name']
        
class Grade(models.Model):
    student = models.ForeignKey("students.Student", on_delete=models.CASCADE, related_name='grades')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='grades')
    marks = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    date_recorded = models.DateField(auto_now_add=True)
    remarks = models.CharField(max_length=200, blank=True)

    class Meta:
        unique_together = ('student', 'subject')
        verbose_name = "Grade"
        verbose_name_plural = "Grades"
        ordering = ['-date_recorded']

    def __str__(self):
        return f"{self.student}: {self.subject} - {self.marks}"

class Assignment(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='assignments')
    class_assigned = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='class_assignments')
    teacher = models.ForeignKey("teachers.Teacher", on_delete=models.CASCADE, related_name='assignments')
    due_date = models.DateTimeField()
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    attachment = models.FileField(upload_to='assignments/%Y/%m/%d/', blank=True, null=True)
    points = models.PositiveIntegerField(default=100, validators=[MaxValueValidator(1000)])
    is_published = models.BooleanField(default=False)

    class Meta:
        ordering = ['-due_date']
        verbose_name = "Assignment"
        verbose_name_plural = "Assignments"

    def __str__(self):
        return f"{self.title} - {self.class_assigned}"

    @property
    def is_past_due(self):
        return timezone.now() > self.due_date

class AssignmentSubmission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey("students.Student", on_delete=models.CASCADE, related_name='submissions')
    submission_date = models.DateTimeField(auto_now_add=True)
    submitted_file = models.FileField(upload_to='submissions/')
    comments = models.TextField(blank=True)
    grade = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    feedback = models.TextField(blank=True)
    is_late = models.BooleanField(default=False)

    class Meta:
        unique_together = ('assignment', 'student')
        ordering = ['-submission_date']
        verbose_name = "Assignment Submission"
        verbose_name_plural = "Assignment Submissions"

    def save(self, *args, **kwargs):
        if not self.pk:  # Only on creation
            self.is_late = timezone.now() > self.assignment.due_date
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student}'s submission for {self.assignment}"