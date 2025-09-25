from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from .forms import UserRegisterForm, UserUpdateForm, AdminProfileForm, StudentProfileForm, TeacherProfileForm, GuardianProfileForm
from .models import CustomUser
from django.urls import reverse
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters

class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    
    def get_success_url(self):
        user = self.request.user
        if user.is_student():
            return reverse('students:student_dashboard') 
        elif user.is_teacher():
            return reverse('teachers:dashboard')
        elif user.is_guardian():
            return reverse('students:guardian_dashboard')
        elif user.is_admin():
            return reverse('admin:index')
        return reverse('home')

class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('accounts:login')  
    template_name = 'accounts/logout.html'  
    
    def dispatch(self, request, *args, **kwargs):
        # Handle both GET and POST requests
        if request.method.lower() == 'get':
            return self.post(request, *args, **kwargs)
        return super().dispatch(request, *args, **kwargs)

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                user = form.save()
                
                # Login the user after registration
                login(request, user)
                messages.success(request, 'Registration successful!')
                
                # Redirect based on role if needed
                if user.is_admin():
                    return redirect('admin:index')
                return redirect('home')
            
            except Exception as e:
                # Log the error for debugging
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error during registration: {str(e)}")
                
                messages.error(request, 'An error occurred during registration. Please try again.')
        else:
            # Add form errors to messages - THIS IS WHAT'S MISSING!
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = UserRegisterForm()
    
    return render(request, 'accounts/register.html', {'form': form})

# Role-specific registration views that all use the same form
# but with different templates and initial data
def student_register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                user = form.save(commit=False)
                user.role = 'student'
                user.save()
                login(request, user)
                messages.success(request, 'Student registration successful!')
                return redirect('students:student_dashboard')
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error during student registration: {str(e)}")
                messages.error(request, 'An error occurred during registration. Please try again.')
        else:
            # Add form errors to messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = UserRegisterForm(initial={'role': 'student'})
    
    return render(request, 'accounts/student_register.html', {'form': form})

def teacher_register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                user = form.save(commit=False)
                user.role = 'teacher'
                user.save()
                login(request, user)
                messages.success(request, 'Teacher registration successful!')
                return redirect('teachers:dashboard')
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error during teacher registration: {str(e)}")
                messages.error(request, 'An error occurred during registration. Please try again.')
        else:
            # Add form errors to messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = UserRegisterForm(initial={'role': 'teacher'})
    
    return render(request, 'accounts/teacher_register.html', {'form': form})

@sensitive_post_parameters('password1', 'password2')
@csrf_protect
def guardian_register(request):
    """
    Handles guardian registration with proper error handling and security measures.
    """
    # Redirect authenticated users away from registration
    if request.user.is_authenticated:
        messages.info(request, "You're already logged in!")
        return redirect('students:guardian_dashboard')
    
    if request.method == 'POST':
        form = UserRegisterForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                user = form.save(commit=False)
                user.role = 'guardian'
                user.is_active = True  # Set to False if email verification needed
                user.save()
                
                # Log the user in after successful registration
                login(request, user)
                
                messages.success(request, 'Guardian registration successful!')
                return redirect('students:guardian_dashboard')
            
            except Exception as e:
                # Log the error for debugging
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error during guardian registration: {str(e)}")
                
                messages.error(request, 'An error occurred during registration. Please try again.')
        else:
            # Add form errors to messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = UserRegisterForm(initial={'role': 'guardian'})
    
    context = {
        'form': form,
        'title': 'Guardian Registration'
    }
    return render(request, 'accounts/guardian_register.html', context)

@login_required
def profile(request):
    user = request.user
    context = {'user': user}
    
    # Add profile information based on role
    if user.is_student() and hasattr(user, 'student_profile'):
        context['profile'] = user.student_profile
    elif user.is_teacher() and hasattr(user, 'teacher_profile'):
        context['profile'] = user.teacher_profile
    elif user.is_guardian() and hasattr(user, 'guardian_profile'):
        context['profile'] = user.guardian_profile
    elif user.is_admin() and hasattr(user, 'admin'):
        context['profile'] = user.admin
    
    return render(request, 'accounts/profile.html', context)

@login_required
def profile_update(request):
    user = request.user
    profile_form = None
    
    # Determine the appropriate profile form based on user role
    if user.is_admin() and hasattr(user, 'admin'):
        profile_form_class = AdminProfileForm
        profile_instance = user.admin
    elif user.is_student() and hasattr(user, 'student'):
        profile_form_class = StudentProfileForm
        profile_instance = user.student
    elif user.is_teacher() and hasattr(user, 'teacher'):
        profile_form_class = TeacherProfileForm
        profile_instance = user.teacher
    elif user.is_guardian() and hasattr(user, 'guardian'):
        profile_form_class = GuardianProfileForm
        profile_instance = user.guardian
    
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, request.FILES, instance=user)
        
        # Initialize profile form if profile exists
        if 'profile_instance' in locals():
            profile_form = profile_form_class(request.POST, instance=profile_instance)
        
        if user_form.is_valid():
            user = user_form.save(commit=False)

            # Handle profile picture
            if 'profile_picture' in request.FILES:
                user.profile_picture = request.FILES['profile_picture']
                
            # Save profile form if it exists and is valid
            if profile_form and profile_form.is_valid():
                profile = profile_form.save(commit=False)
                profile.user = user
                profile.save()
            
            user.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('accounts:profile')
    else:
        user_form = UserUpdateForm(instance=user)
        if 'profile_instance' in locals():
            profile_form = profile_form_class(instance=profile_instance)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form
    }
    return render(request, 'accounts/profile_update.html', context)