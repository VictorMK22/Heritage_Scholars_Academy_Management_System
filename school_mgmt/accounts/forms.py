from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser, Admin
from django.core.exceptions import ValidationError
from students.models import Student, Guardian
from teachers.models import Teacher

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=15, required=False)
    role = forms.ChoiceField(choices=CustomUser.ROLE_CHOICES)
    
    # Student-specific
    admission_number = forms.CharField(max_length=20, required=False)
    
    # Teacher/Admin-specific
    employee_id = forms.CharField(max_length=20, required=False)
    
    # Guardian-specific
    occupation = forms.CharField(max_length=100, required=False)
    
    # Admin-specific
    department = forms.CharField(max_length=100, required=False)

    class Meta:
        model = CustomUser
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'password1', 'password2', 'role', 'phone',
            'admission_number', 'employee_id', 'occupation', 'department'
        ]

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        
        if role == 'student' and not cleaned_data.get('admission_number'):
            raise ValidationError("Admission number is required for students")
        elif role in ['teacher', 'admin'] and not cleaned_data.get('employee_id'):
            raise ValidationError("Employee ID is required")
        elif role == 'guardian' and not cleaned_data.get('occupation'):
            raise ValidationError("Occupation is required")
        elif role == 'admin' and not cleaned_data.get('department'):
            cleaned_data['department'] = "Administration"  # Default
        
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        role = self.cleaned_data.get('role')
        
        # Set admin permissions if role is admin
        if role == 'admin':
            user.is_staff = True
            user.is_superuser = True
        
        if commit:
            user.save()
            self.save_m2m()  # Only needed if using many-to-many fields
            
        return user

class UserUpdateForm(forms.ModelForm):
    profile_picture = forms.ImageField(required=False)
    class Meta:
        model = CustomUser
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'phone', 'address', 'date_of_birth', 'profile_picture'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }

class AdminProfileForm(forms.ModelForm):
    class Meta:
        model = Admin
        fields = ['employee_id', 'department']

class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['admission_number']

class TeacherProfileForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = ['employee_id']

class GuardianProfileForm(forms.ModelForm):
    class Meta:
        model = Guardian
        fields = ['address', 'relationship_to_student']