from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.db.models import Prefetch, Q
from django.db import transaction
from django.db.models import Subquery, OuterRef, F, Value
from django.db.models.functions import Concat

from teachers.models import Teacher
from students.models import Student
from .models import Class, Subject, ClassTeaching, Grade, Assignment, AssignmentSubmission
from .forms import (ClassForm, ClassTeacherAssignmentForm, ClassSubjectAssignmentForm, SubjectForm, AssignmentForm, 
                   SubmissionForm, GradeForm, GradeSubmissionForm)
from .utils import current_academic_year

# Class Views
class ClassListView(LoginRequiredMixin, ListView):
    model = Class
    template_name = 'academics/class_list.html'
    context_object_name = 'classes'

    def get_queryset(self):
        return Class.objects.prefetch_related(
            'teaching_assignments__teacher__user',
            'teaching_assignments__subjects'
        ).all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        class_data = []
        
        for class_obj in context['classes']:
            # Get primary teacher assignment
            primary_assignment = class_obj.teaching_assignments.filter(
                is_primary=True
            ).first()
            
            # Get all unique subjects through teaching assignments
            subjects = []
            subject_ids = set()
            
            for assignment in class_obj.teaching_assignments.all():
                for subject in assignment.subjects.all():
                    if subject.id not in subject_ids:
                        subjects.append(subject)
                        subject_ids.add(subject.id)
            
            class_data.append({
                'class': class_obj,
                'primary_teacher': primary_assignment.teacher if primary_assignment else None,
                'subjects': subjects
            })
        
        context['class_data'] = class_data
        return context


class ClassCreateView(LoginRequiredMixin, CreateView):
    model = Class
    form_class = ClassForm
    template_name = 'academics/class_form.html'
    success_url = reverse_lazy('academics:class_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Class created successfully!')
        return super().form_valid(form)

class ClassDetailView(LoginRequiredMixin, DetailView):
    model = Class
    template_name = 'academics/class_detail.html'
    context_object_name = 'class_obj'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        class_obj = self.object
        
        # Get all teaching assignments with optimized queries
        teaching_assignments = class_obj.teaching_assignments.select_related(
            'teacher__user'
        ).prefetch_related(
            'subjects'
        ).order_by('-is_primary', 'teacher__user__last_name')
        
        # Get unique subjects with their primary teachers
        subjects_data = []
        seen_subjects = set()
        
        for assignment in teaching_assignments:
            teacher_name = assignment.teacher.user.get_full_name()
            for subject in assignment.subjects.all():
                if subject.id not in seen_subjects:
                    subjects_data.append({
                        'subject': subject,
                        'teacher_name': teacher_name,
                        'is_primary': assignment.is_primary,
                        'teacher_id': assignment.teacher.id
                    })
                    seen_subjects.add(subject.id)
        
        context.update({
            'teaching_assignments': teaching_assignments,
            'subjects_data': sorted(subjects_data, key=lambda x: x['subject'].name),
            'teacher_count': teaching_assignments.count(),
            'student_count': class_obj.student_set.count(),
            'primary_teacher': next(
                (ta.teacher for ta in teaching_assignments if ta.is_primary), 
                None
            ),
            'page_title': f"{class_obj.name} - Class Details"
        })
        return context
    
class ClassAssignTeachersView(LoginRequiredMixin, UpdateView):
    model = Class
    form_class = ClassTeacherAssignmentForm
    template_name = 'academics/class_assign_teachers.html'
    
    @transaction.atomic
    def get_initial(self):
        """Prefill the form with currently assigned teachers"""
        initial = super().get_initial()
        initial['teachers'] = list(self.object.teachers.values_list('id', flat=True))
        return initial
    
    @transaction.atomic
    def form_valid(self, form):
        """Handle successful form submission with proper teacher assignments"""
        class_obj = self.object
        selected_teachers = form.cleaned_data['teachers']
        
        # Clear existing assignments
        ClassTeaching.objects.filter(classroom=class_obj).delete()
        
        # Create new assignments with first teacher as primary
        if selected_teachers:
            # Assign first teacher as primary
            primary_teacher = selected_teachers[0]
            ClassTeaching.objects.create(
                classroom=class_obj,
                teacher=primary_teacher,
                is_primary=True
            )
            
            # Assign remaining teachers as non-primary
            for teacher in selected_teachers[1:]:
                ClassTeaching.objects.create(
                    classroom=class_obj,
                    teacher=teacher,
                    is_primary=False
                )
        
        messages.success(self.request, 'Teachers assigned successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        """Redirect back to class update page after assignment"""
        return reverse('academics:class_update', kwargs={'pk': self.object.pk})

class ClassAssignSubjectsView(LoginRequiredMixin, UpdateView):
    model = Class
    form_class = ClassSubjectAssignmentForm
    template_name = 'academics/class_assign_subjects.html'

    @transaction.atomic
    def form_valid(self, form):
        class_obj = self.object
        
        # Check if any teachers are assigned
        if not class_obj.teaching_assignments.exists():
            messages.error(self.request, 
                         'Please assign at least one teacher to this class before assigning subjects')
            return self.form_invalid(form)
        
        # Get selected subjects
        selected_subjects = form.cleaned_data['subjects']
        
        # Update subjects for all teaching assignments
        for assignment in class_obj.teaching_assignments.all():
            assignment.subjects.set(selected_subjects)
        
        # Update class_assigned field for each subject
        Subject.objects.filter(pk__in=[s.pk for s in selected_subjects]).update(
            class_assigned=class_obj
        )
        
        # Clear class_assigned for deselected subjects
        Subject.objects.filter(class_assigned=class_obj).exclude(
            pk__in=[s.pk for s in selected_subjects]
        ).update(class_assigned=None)
        
        messages.success(self.request, 'Subjects assigned successfully!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('academics:class_detail', kwargs={'pk': self.object.pk})
    
class ClassUpdateView(LoginRequiredMixin, UpdateView):
    model = Class
    form_class = ClassForm
    template_name = 'academics/class_form.html'
    success_url = reverse_lazy('academics:class_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Class updated successfully!')
        return super().form_valid(form)

class ClassDeleteView(LoginRequiredMixin, DeleteView):
    model = Class
    template_name = 'academics/class_confirm_delete.html'
    success_url = reverse_lazy('academics:class_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Class deleted successfully!')
        return super().delete(request, *args, **kwargs)

# Subject Views
class SubjectListView(LoginRequiredMixin, ListView):
    model = Subject
    template_name = 'academics/subject_list.html'
    context_object_name = 'subjects'

    def get_queryset(self):
        return Subject.objects.select_related(
            'class_assigned',
            'teacher__user'
        ).prefetch_related(
            'classteaching_set__classroom'
        ).all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        subject_data = []
        
        for subject in context['subjects']:
            # Get all classes this subject is assigned to
            classes = []
            if subject.class_assigned:
                classes.append(subject.class_assigned)
            classes.extend([ct.classroom for ct in subject.classteaching_set.all()])
            
            # Remove duplicates
            seen = set()
            unique_classes = []
            for cls in classes:
                if cls.id not in seen:
                    seen.add(cls.id)
                    unique_classes.append(cls)
            
            subject_data.append({
                'subject': subject,
                'classes': unique_classes,
                'teacher': subject.teacher
            })
        
        context['subject_data'] = subject_data
        return context

class SubjectCreateView(LoginRequiredMixin, CreateView):
    model = Subject
    form_class = SubjectForm
    template_name = 'academics/subject_form.html'
    success_url = reverse_lazy('academics:subject_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Subject created successfully!')
        return super().form_valid(form)

class SubjectDetailView(LoginRequiredMixin, DetailView):
    model = Subject
    template_name = 'academics/subject_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['assignments'] = self.object.assignments.all()
        context['grades'] = Grade.objects.filter(subject=self.object)
        return context

class SubjectUpdateView(LoginRequiredMixin, UpdateView):
    model = Subject
    form_class = SubjectForm
    template_name = 'academics/subject_form.html'
    success_url = reverse_lazy('academics:subject_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Subject updated successfully!')
        return super().form_valid(form)

class SubjectDeleteView(LoginRequiredMixin, DeleteView):
    model = Subject
    template_name = 'academics/subject_confirm_delete.html'
    success_url = reverse_lazy('academics:subject_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Subject deleted successfully!')
        return super().delete(request, *args, **kwargs)

# Assignment Views
class AssignmentListView(LoginRequiredMixin, ListView):
    model = Assignment
    template_name = 'academics/assignment_list.html'
    context_object_name = 'assignments'
    
    def get_queryset(self):
        queryset = Assignment.objects.select_related(
            'class_assigned', 'subject'
        ).order_by('-due_date')
        
        # Filter by class if provided
        class_id = self.request.GET.get('class_id')
        if class_id:
            queryset = queryset.filter(class_assigned_id=class_id)
            
        # Filter by subject if provided
        subject_id = self.request.GET.get('subject_id')
        if subject_id:
            queryset = queryset.filter(subject_id=subject_id)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['classes'] = Class.objects.all()
        context['subjects'] = Subject.objects.all()
        return context

class AssignmentCreateView(LoginRequiredMixin, CreateView):
    model = Assignment
    form_class = AssignmentForm
    template_name = 'academics/assignment_form.html'
    
    def get_form_kwargs(self):
        """Pass the request to the form"""
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add context for the template to show helpful messages
        try:
            teacher = self.request.user.teacher_profile
            current_year = current_academic_year()
            year_var = current_year.split('-')[0] if '-' in current_year else current_year
            
            current_subjects = teacher.subjects.filter(academic_year=year_var)
            context['has_current_subjects'] = current_subjects.exists()
            context['current_academic_year'] = current_year
            
        except Teacher.DoesNotExist:
            context['has_current_subjects'] = False
            
        return context
    
    def form_valid(self, form):
        try:
            teacher = self.request.user.teacher_profile
            
            # Assign the current teacher to the assignment
            form.instance.teacher = teacher
            
            # Set academic year based on the selected subject
            if form.cleaned_data.get('subject'):
                form.instance.academic_year = form.cleaned_data['subject'].academic_year
            
            response = super().form_valid(form)
            messages.success(self.request, "Assignment created successfully!")
            return response
            
        except Teacher.DoesNotExist:
            messages.error(self.request, "You must be a teacher to create assignments.")
            return self.form_invalid(form)
    
    def get_success_url(self):
        return reverse('teachers:dashboard')

class AssignmentDetailView(LoginRequiredMixin, DetailView):
    model = Assignment
    template_name = 'academics/assignment_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['submissions'] = self.object.submissions.all()
        context['can_submit'] = not self.object.is_past_due
        return context

class AssignmentUpdateView(LoginRequiredMixin, UpdateView):
    model = Assignment
    form_class = AssignmentForm
    template_name = 'academics/assignment_form.html'
    
    def get_success_url(self):
        return reverse_lazy('academics:assignment_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, 'Assignment updated successfully!')
        return super().form_valid(form)

class AssignmentDeleteView(LoginRequiredMixin, DeleteView):
    model = Assignment
    template_name = 'academics/assignment_confirm_delete.html'
    success_url = reverse_lazy('academics:assignment_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Assignment deleted successfully!')
        return super().delete(request, *args, **kwargs)

# Submission Views
class SubmissionListView(LoginRequiredMixin, ListView):
    model = AssignmentSubmission
    template_name = 'academics/submission_list.html'
    context_object_name = 'submissions'
    
    def get_queryset(self):
        queryset = AssignmentSubmission.objects.select_related(
            'assignment', 'student__user'
        ).order_by('-submission_date')
        
        # Filter by assignment if provided
        assignment_id = self.request.GET.get('assignment_id')
        if assignment_id:
            queryset = queryset.filter(assignment_id=assignment_id)
            
        # Filter by student if provided
        student_id = self.request.GET.get('student_id')
        if student_id:
            queryset = queryset.filter(student_id=student_id)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['assignments'] = Assignment.objects.all()
        context['students'] = Student.objects.all()
        return context

class SubmissionCreateView(LoginRequiredMixin, CreateView):
    model = AssignmentSubmission
    form_class = SubmissionForm
    template_name = 'academics/submission_form.html'
    
    def get_initial(self):
        initial = super().get_initial()
        assignment = get_object_or_404(Assignment, pk=self.kwargs['assignment_id'])
        initial['assignment'] = assignment
        return initial
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['student'] = self.request.user.student_profile
        return kwargs
    
    def get_success_url(self):
        return reverse_lazy('academics:submission_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        form.instance.student = self.request.user.student_profile
        messages.success(self.request, 'Assignment submitted successfully!')
        return super().form_valid(form)

class SubmissionDetailView(LoginRequiredMixin, DetailView):
    model = AssignmentSubmission
    template_name = 'academics/submission_detail.html'
    context_object_name = 'submission'

class SubmissionUpdateView(LoginRequiredMixin, UpdateView):
    model = AssignmentSubmission
    form_class = SubmissionForm
    template_name = 'academics/submission_form.html'
    
    def get_success_url(self):
        return reverse_lazy('academics:submission_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, 'Submission updated successfully!')
        return super().form_valid(form)

class SubmissionDeleteView(LoginRequiredMixin, DeleteView):
    model = AssignmentSubmission
    template_name = 'academics/submission_confirm_delete.html'
    success_url = reverse_lazy('academics:submission_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Submission deleted successfully!')
        return super().delete(request, *args, **kwargs)

class SubmissionGradeView(LoginRequiredMixin, UpdateView):
    model = AssignmentSubmission
    form_class = GradeSubmissionForm
    template_name = 'academics/submission_grade_form.html'
    
    def get_success_url(self):
        return reverse_lazy('academics:submission_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, 'Grade submitted successfully!')
        return super().form_valid(form)

# Grade Views
class GradeListView(LoginRequiredMixin, ListView):
    model = Grade
    template_name = 'academics/grade_list.html'
    context_object_name = 'grades'
    
    def get_queryset(self):
        queryset = Grade.objects.select_related(
            'student__user', 'subject'
        ).order_by('-subject')
        
        # Filter by student if provided
        student_id = self.request.GET.get('student_id')
        if student_id:
            queryset = queryset.filter(student_id=student_id)
            
        # Filter by subject if provided
        subject_id = self.request.GET.get('subject_id')
        if subject_id:
            queryset = queryset.filter(subject_id=subject_id)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['students'] = Student.objects.all()
        context['subjects'] = Subject.objects.all()
        return context

class GradeCreateView(LoginRequiredMixin, CreateView):
    model = Grade
    form_class = GradeForm
    template_name = 'academics/grade_form.html'
    success_url = reverse_lazy('academics:grade_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Grade created successfully!')
        return super().form_valid(form)

class GradeDetailView(LoginRequiredMixin, DetailView):
    model = Grade
    template_name = 'academics/grade_detail.html'
    context_object_name = 'grade'
    
    def get_queryset(self):
        return Grade.objects.all()

class GradeUpdateView(LoginRequiredMixin, UpdateView):
    model = Grade
    form_class = GradeForm
    template_name = 'academics/grade_form.html'
    success_url = reverse_lazy('academics:grade_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Grade updated successfully!')
        return super().form_valid(form)

class GradeDeleteView(LoginRequiredMixin, DeleteView):
    model = Grade
    template_name = 'academics/grade_confirm_delete.html'
    success_url = reverse_lazy('academics:grade_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Grade deleted successfully!')
        return super().delete(request, *args, **kwargs)

# Class-specific Views
class ClassSubjectListView(LoginRequiredMixin, ListView):
    template_name = 'academics/class_subject_list.html'
    context_object_name = 'subjects'
    
    def get_queryset(self):
        self.class_obj = get_object_or_404(Class, pk=self.kwargs['class_id'])
        return Subject.objects.filter(class_assigned=self.class_obj)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['class'] = self.class_obj
        return context

class ClassAssignmentListView(LoginRequiredMixin, ListView):
    template_name = 'academics/class_assignment_list.html'
    context_object_name = 'assignments'
    
    def get_queryset(self):
        self.class_obj = get_object_or_404(Class, pk=self.kwargs['class_id'])
        return Assignment.objects.filter(class_assigned=self.class_obj)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['class'] = self.class_obj
        return context

class ClassGradeListView(LoginRequiredMixin, ListView):
    template_name = 'academics/class_grade_list.html'
    context_object_name = 'grades'
    
    def get_queryset(self):
        self.class_obj = get_object_or_404(Class, pk=self.kwargs['class_id'])
        subjects = Subject.objects.filter(class_assigned=self.class_obj)
        return Grade.objects.filter(subject__in=subjects)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['class'] = self.class_obj
        return context

# Student-specific Views
class StudentGradeListView(LoginRequiredMixin, ListView):
    template_name = 'academics/student_grade_list.html'
    context_object_name = 'grades'
    
    def get_queryset(self):
        self.student = get_object_or_404(Student, pk=self.kwargs['student_id'])
        return Grade.objects.filter(student=self.student)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['student'] = self.student
        return context

class StudentAssignmentListView(LoginRequiredMixin, ListView):
    template_name = 'academics/student_assignment_list.html'
    context_object_name = 'assignments'
    
    def get_queryset(self):
        self.student = get_object_or_404(Student, pk=self.kwargs['student_id'])
        return Assignment.objects.filter(class_assigned=self.student.current_class)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['student'] = self.student
        
        # Add submission status for each assignment
        assignments = []
        for assignment in context['assignments']:
            submission = AssignmentSubmission.objects.filter(
                assignment=assignment,
                student=self.student
            ).first()
            assignments.append({
                'assignment': assignment,
                'submission': submission,
                'submitted': submission is not None,
                'graded': submission.grade if submission else None
            })
        
        context['assignments'] = assignments
        return context

class StudentSubmissionListView(LoginRequiredMixin, ListView):
    template_name = 'academics/student_submission_list.html'
    context_object_name = 'submissions'
    
    def get_queryset(self):
        self.student = get_object_or_404(Student, pk=self.kwargs['student_id'])
        return AssignmentSubmission.objects.filter(student=self.student)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['student'] = self.student
        return context

# Teacher-specific Views
class TeacherClassListView(LoginRequiredMixin, ListView):
    template_name = 'academics/teacher_class_list.html'
    context_object_name = 'classes'
    
    def get_queryset(self):
        self.teacher = get_object_or_404(Teacher, pk=self.kwargs['teacher_id'])
        return Class.objects.filter(teacher=self.teacher)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['teacher'] = self.teacher
        return context

class TeacherAssignmentListView(LoginRequiredMixin, ListView):
    template_name = 'academics/teacher_assignment_list.html'
    context_object_name = 'assignments'
    
    def get_queryset(self):
        self.teacher = get_object_or_404(Teacher, pk=self.kwargs['teacher_id'])
        classes = Class.objects.filter(teacher=self.teacher)
        return Assignment.objects.filter(class_assigned__in=classes)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['teacher'] = self.teacher
        return context

# API Views
from rest_framework.generics import ListAPIView, RetrieveAPIView
from .serializers import ClassSerializer, AssignmentSerializer

class ClassListAPI(ListAPIView):
    queryset = Class.objects.all()
    serializer_class = ClassSerializer

class ClassDetailAPI(RetrieveAPIView):
    queryset = Class.objects.all()
    serializer_class = ClassSerializer

class AssignmentListAPI(ListAPIView):
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer

class AssignmentDetailAPI(RetrieveAPIView):
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer