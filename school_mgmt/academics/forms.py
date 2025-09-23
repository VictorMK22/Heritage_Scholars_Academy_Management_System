from django import forms
from django.db.models import Q
from django.utils import timezone
from teachers.models import Teacher, TeacherSubjectAssignment
from .models import Class, ClassTeaching, Subject, Grade, Assignment, AssignmentSubmission
from .utils import current_academic_year

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
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        help_text="Due date and time for the assignment"
    )
    
    # Make fields required and add Bootstrap classes
    title = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter assignment title'}),
        max_length=200
    )
    
    description = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Enter assignment description'}),
        required=False
    )
    
    points = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '1000'}),
        initial=100
    )

    class Meta:
        model = Assignment
        fields = ['title', 'description', 'subject', 'class_assigned', 
                'due_date', 'attachment', 'points', 'is_published']
        widgets = {
            'subject': forms.Select(attrs={'class': 'form-select'}),
            'class_assigned': forms.Select(attrs={'class': 'form-select'}),
            'attachment': forms.FileInput(attrs={'class': 'form-control'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        # Add Bootstrap classes to all fields
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                if isinstance(field.widget, forms.Select):
                    field.widget.attrs['class'] = 'form-select'
                elif isinstance(field.widget, forms.CheckboxInput):
                    field.widget.attrs['class'] = 'form-check-input'
                else:
                    field.widget.attrs['class'] = 'form-control'
        
        if self.request and hasattr(self.request.user, 'teacher_profile'):
            try:
                teacher = self.request.user.teacher_profile
                current_year = current_academic_year()
                year_var = current_year.split('-')[0] if '-' in current_year else current_year
                
                print(f"=== DEBUG FORM INIT ===")
                print(f"Teacher: {teacher.full_name} (ID: {teacher.id})")
                print(f"Current year: {current_year}")
                print(f"Year var: {year_var}")
                
                # DEBUG 1: Check what TeacherSubjectAssignment records exist
                assignments = TeacherSubjectAssignment.objects.filter(teacher=teacher)
                print(f"TeacherSubjectAssignment records: {assignments.count()}")
                for assignment in assignments:
                    print(f"  - {assignment.subject.name} (Year: {assignment.academic_year})")
                
                # DEBUG 2: Check what subjects exist in system
                all_subjects = Subject.objects.all()
                print(f"All subjects in system: {all_subjects.count()}")
                for subject in all_subjects:
                    print(f"  - {subject.name} (Year: {subject.academic_year})")
                
                # Try multiple query approaches to find the right one
                
                # Approach 1: Using TeacherSubjectAssignment (through model)
                print("=== Approach 1: Through TeacherSubjectAssignment ===")
                current_subjects_1 = Subject.objects.filter(
                    teacher_assignments__teacher=teacher,
                    teacher_assignments__academic_year=year_var
                ).distinct()
                print(f"Found {current_subjects_1.count()} subjects")
                
                # Approach 2: Using direct ManyToMany relationship
                print("=== Approach 2: Direct ManyToMany ===")
                current_subjects_2 = Subject.objects.filter(
                    teachers=teacher,  # Direct M2M relationship
                    academic_year=year_var
                ).distinct()
                print(f"Found {current_subjects_2.count()} subjects")
                
                # Approach 3: Get assignment IDs first, then subjects
                print("=== Approach 3: Via assignment IDs ===")
                assignment_ids = TeacherSubjectAssignment.objects.filter(
                    teacher=teacher,
                    academic_year=year_var
                ).values_list('subject_id', flat=True)
                current_subjects_3 = Subject.objects.filter(id__in=assignment_ids)
                print(f"Found {current_subjects_3.count()} subjects")
                
                # Approach 4: Try without academic year filter first
                print("=== Approach 4: Without academic year filter ===")
                current_subjects_4 = Subject.objects.filter(teachers=teacher).distinct()
                print(f"Found {current_subjects_4.count()} subjects (all years)")
                for subj in current_subjects_4:
                    print(f"  - {subj.name} ({subj.academic_year})")
                
                # Approach 5: Try different academic year formats
                print("=== Approach 5: Different year formats ===")
                year_formats_to_try = [year_var, current_year, str(int(year_var)), year_var + '-01']
                for year_format in year_formats_to_try:
                    subjects = Subject.objects.filter(
                        teachers=teacher,
                        academic_year=year_format
                    ).distinct()
                    print(f"Year format '{year_format}': {subjects.count()} subjects")
                
                # Use the approach that finds results
                if current_subjects_1.exists():
                    current_subjects = current_subjects_1
                    print("Using Approach 1")
                elif current_subjects_2.exists():
                    current_subjects = current_subjects_2
                    print("Using Approach 2")
                elif current_subjects_3.exists():
                    current_subjects = current_subjects_3
                    print("Using Approach 3")
                else:
                    current_subjects = current_subjects_4  # All subjects for this teacher
                    print("Using Approach 4 (all subjects for teacher)")
                
                print(f"Final subjects count: {current_subjects.count()}")
                for subject in current_subjects:
                    print(f"  - {subject.name} ({subject.academic_year})")
                
                # Get classes using multiple approaches
                print("=== Getting Classes ===")
                
                # Approach 1: Through ClassTeaching
                current_classes_1 = Class.objects.filter(
                    teaching_assignments__teacher=teacher,
                    teaching_assignments__subjects__in=current_subjects
                ).distinct()
                print(f"Approach 1 classes: {current_classes_1.count()}")
                
                # Approach 2: Direct from ClassTeaching
                current_classes_2 = Class.objects.filter(
                    teaching_assignments__teacher=teacher
                ).distinct()
                print(f"Approach 2 classes: {current_classes_2.count()}")
                
                # Use the approach that finds results
                if current_classes_1.exists():
                    current_classes = current_classes_1
                else:
                    current_classes = current_classes_2
                
                print(f"Final classes count: {current_classes.count()}")
                for cls in current_classes:
                    print(f"  - {cls.name}")
                
                # Apply to form fields
                self.fields['subject'].queryset = current_subjects
                self.fields['class_assigned'].queryset = current_classes
                
                # Add help text based on results
                if not current_subjects.exists():
                    self.fields['subject'].help_text = f"No subjects found. Teacher has {assignments.count()} total assignments."
                else:
                    self.fields['subject'].help_text = f"Found {current_subjects.count()} subjects"
                    
                if not current_classes.exists():
                    self.fields['class_assigned'].help_text = "No classes assigned"
                else:
                    self.fields['class_assigned'].help_text = f"Found {current_classes.count()} classes"
                
                print("=== DEBUG END ===")
                
            except Teacher.DoesNotExist:
                self.fields['subject'].queryset = Subject.objects.none()
                self.fields['class_assigned'].queryset = Class.objects.none()
                print("DEBUG: Teacher.DoesNotExist")
            except Exception as e:
                self.fields['subject'].queryset = Subject.objects.none()
                self.fields['class_assigned'].queryset = Class.objects.none()
                print(f"DEBUG: Exception: {e}")
        else:
            self.fields['subject'].queryset = Subject.objects.none()
            self.fields['class_assigned'].queryset = Class.objects.none()
            print("DEBUG: User is not a teacher or no teacher_profile")

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