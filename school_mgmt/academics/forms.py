from django import forms
from django.db.models import Q
from django.utils import timezone
from teachers.models import Teacher
from .models import Class, ClassTeaching, Subject, Grade, Assignment, AssignmentSubmission

class ClassForm(forms.ModelForm):
    teachers = forms.ModelMultipleChoiceField(
        queryset=Teacher.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control'})
    )
    subjects = forms.ModelMultipleChoiceField(
        queryset=Subject.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Class
        fields = ['name', 'teachers', 'subjects']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['teachers'].initial = self.instance.teachers.all()
            self.fields['subjects'].initial = Subject.objects.filter(
                classteaching__classroom=self.instance
            ).distinct()

    def save(self, commit=True):
        instance = super().save(commit=commit)
        if commit:
            # Clear existing assignments
            ClassTeaching.objects.filter(classroom=instance).delete()
            # Create new assignments
            for teacher in self.cleaned_data['teachers']:
                teaching = ClassTeaching.objects.create(
                    classroom=instance,
                    teacher=teacher,
                    is_primary=False  # You can modify this logic
                )
                teaching.subjects.set(self.cleaned_data['subjects'])
        return instance

class ClassTeacherAssignmentForm(forms.ModelForm):
    teachers = forms.ModelMultipleChoiceField(
        queryset=Teacher.objects.all().select_related('user'),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="First selected teacher will be marked as primary"
    )
    
    class Meta:
        model = Class
        fields = []
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['teachers'].initial = self.instance.teachers.values_list('id', flat=True)
    
    def clean(self):
        cleaned_data = super().clean()
        teachers = cleaned_data.get('teachers', [])
        
        # Ensure at least one teacher is selected if none currently assigned
        if not teachers and self.instance.teachers.count() == 0:
            raise ValidationError("At least one teacher must be assigned to the class")
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        with transaction.atomic():
            # Clear existing assignments
            ClassTeaching.objects.filter(classroom=instance).delete()
            
            # Create new assignments
            teachers = self.cleaned_data.get('teachers', [])
            for i, teacher in enumerate(teachers):
                ClassTeaching.objects.create(
                    classroom=instance,
                    teacher=teacher,
                    is_primary=(i == 0)  # First teacher is primary
                )
        
        if commit:
            instance.save()
        return instance

class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'class_assigned', 'term', 'teacher']
        widgets = {
            'class_assigned': forms.Select(attrs={'class': 'form-control'}),
            'teacher': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['teacher'].queryset = Teacher.objects.all()
        self.fields['class_assigned'].queryset = Class.objects.all()

class ClassSubjectAssignmentForm(forms.ModelForm):
    subjects = forms.ModelMultipleChoiceField(
        queryset=Subject.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = Class
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            # Get subjects assigned through any method
            self.fields['subjects'].initial = Subject.objects.filter(
                Q(class_assigned=self.instance) |
                Q(classteaching__classroom=self.instance)
            ).distinct()

class AssignmentForm(forms.ModelForm):
    due_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        help_text="Due date and time for the assignment"
    )

    class Meta:
        model = Assignment
        fields = ['title', 'description', 'subject', 'class_assigned', 
                'due_date', 'attachment', 'points', 'is_published']

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        if self.request and hasattr(self.request.user, 'teacher_profile'):
            teacher = self.request.user.teacher_profile
            self.fields['subject'].queryset = teacher.subjects.all()
            self.fields['class_assigned'].queryset = Class.objects.filter(
                teaching_assignments__teacher=teacher
            ).distinct()

    def clean_due_date(self):
        due_date = self.cleaned_data['due_date']
        if due_date < timezone.now():
            raise forms.ValidationError("Due date cannot be in the past")
        return due_date

class SubmissionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        student = kwargs.pop('student', None)
        super().__init__(*args, **kwargs)
        if student:
            self.fields['assignment'].queryset = Assignment.objects.filter(
                class_assigned=student.current_class
            )
    
    class Meta:
        model = AssignmentSubmission
        fields = ['assignment', 'submitted_file', 'comments']
        widgets = {
            'assignment': forms.Select(attrs={'class': 'form-select'}),
            'comments': forms.Textarea(attrs={'rows': 3}),
        }

class GradeSubmissionForm(forms.ModelForm):
    class Meta:
        model = AssignmentSubmission
        fields = ['grade', 'feedback']
        widgets = {
            'feedback': forms.Textarea(attrs={'rows': 3}),
        }

class GradeForm(forms.ModelForm):
    class Meta:
        model = Grade
        fields = ['student', 'subject', 'marks']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select'}),
            'subject': forms.Select(attrs={'class': 'form-select'}),
        }