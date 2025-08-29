from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from accounts.decorators import student_required, guardian_required
from academics.models import Subject, Assignment, AssignmentSubmission  
from .models import Student
from accounts.models import CustomUser
from django.contrib import messages

@login_required
@student_required
def student_dashboard(request):
    student = request.user.student_profile
    
    # Get basic student info
    context = {
        'student': student,
        'current_class': student.current_class,
        'class_teacher': student.current_class.get_primary_teacher() if student.current_class else None,
        'attendance_percentage': student.attendance_percentage,
    }

    # Get assignments data
    if student.current_class:
        pending_assignments = Assignment.objects.filter(
            class_assigned=student.current_class
        ).exclude(
            pk__in=AssignmentSubmission.objects.filter(
                student=student
            ).values_list('assignment__pk', flat=True)
        ).order_by('due_date')[:5]

        submitted_assignments = AssignmentSubmission.objects.filter(
            student=student
        ).select_related('assignment').order_by('-submission_date')[:5]

        context.update({
            'pending_assignments': pending_assignments,
            'submitted_assignments': submitted_assignments,
            'pending_count': pending_assignments.count(),
            'submitted_count': submitted_assignments.count(),
        })
    else:
        context.update({
            'pending_assignments': [],
            'submitted_assignments': [],
            'pending_count': 0,
            'submitted_count': 0,
        })

    return render(request, 'students/student_dashboard.html', context)

@login_required
@student_required
def student_subject_list(request):
    student = request.user.student_profile
    current_class = student.current_class
    subjects = Subject.objects.filter(class_assigned=current_class)
    
    context = {
        'subjects': subjects,
        'current_class': current_class,
    }
    return render(request, 'students/student_subject_list.html', context)

@login_required
@student_required
def student_assignment_list(request):
    student = request.user.student_profile
    current_class = student.current_class
    assignments = Assignment.objects.filter(
        class_assigned=current_class
    ).order_by('-due_date')
    
    # Add submission status for each assignment
    for assignment in assignments:
        assignment.submitted = assignment.submissions.filter(student=student).exists()
    
    context = {
        'assignments': assignments,
    }
    return render(request, 'students/student_assignment_list.html', context)

@login_required
def assign_students_to_class(request):
    if request.method == 'POST':
        class_id = request.POST.get('class_id')
        student_ids = request.POST.getlist('student_ids')
        
        try:
            class_obj = Class.objects.get(pk=class_id)
            students = Student.objects.filter(pk__in=student_ids)
            
            # Update all selected students
            updated = students.update(current_class=class_obj)
            
            messages.success(request, f'Successfully assigned {updated} students to {class_obj.name}')
            return redirect('students:student_admin')
            
        except Class.DoesNotExist:
            messages.error(request, 'Selected class does not exist')
    
    # For GET requests, show the assignment form
    classes = Class.objects.all()
    unassigned_students = Student.objects.filter(current_class__isnull=True)
    
    context = {
        'classes': classes,
        'students': unassigned_students
    }
    return render(request, 'students/assign_to_class.html', context)


@login_required
@guardian_required
def guardian_dashboard(request):
    guardian = request.user.guardian_profile
    # Assuming Guardian model has a related_name='ward_students' for students
    students = guardian.ward_students.all()  
    recent_activities = []
    
    for student in students:
        recent_activities.extend(
            student.submissions.order_by('-submission_date')[:3]
        )
    
    context = {
        'guardian': guardian,
        'students': students,
        'recent_activities': recent_activities[:5],  # Show only 5 most recent
    }
    return render(request, 'students/guardian_dashboard.html', context)

@login_required
@guardian_required
def guardian_student_list(request):
    guardian = request.user.guardian_profile
    students = guardian.ward_students.all().select_related('current_class')
    
    context = {
        'students': students,
    }
    return render(request, 'students/guardian_student_list.html', context)

@login_required
@guardian_required
def guardian_student_grades(request, student_id):
    guardian = request.user.guardian_profile
    student = get_object_or_404(Student, id=student_id)
    
    # Verify the student is under this guardian's care
    if student.guardian != guardian:
        return HttpResponseForbidden("You don't have permission to view this student's grades")
    
    # Assuming Grade model exists with student ForeignKey
    grades = student.grade_set.select_related('course').order_by('-date_given')
    
    context = {
        'student': student,
        'grades': grades,
    }
    return render(request, 'students/guardian_student_grades.html', context)

@login_required
@guardian_required
def guardian_student_classes(request):
    guardian = request.user.guardian_profile
    students = guardian.ward_students.select_related('current_class')
    
    context = {
        'students': students,
    }
    return render(request, 'students/guardian_student_classes.html', context)

@login_required
@guardian_required
def guardian_student_attendance(request, student_id):
    guardian = request.user.guardian_profile
    student = get_object_or_404(Student, id=student_id)
    
    # Verify the student is under this guardian's care
    if student.guardian != guardian:
        return HttpResponseForbidden("You don't have permission to view this student's attendance")
    
    # Assuming Attendance model exists
    attendance_records = student.attendance_records.order_by('-date')
    
    # Calculate attendance stats
    total_days = attendance_records.count()
    present_days = attendance_records.filter(status='present').count()
    attendance_percentage = (present_days / total_days * 100) if total_days > 0 else 0
    
    context = {
        'student': student,
        'attendance_records': attendance_records[:30],  # Last 30 records
        'attendance_stats': {
            'total_days': total_days,
            'present_days': present_days,
            'percentage': round(attendance_percentage, 2)
        }
    }
    return render(request, 'students/guardian_student_attendance.html', context)