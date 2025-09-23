from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from accounts.decorators import student_required, guardian_required
from academics.models import Subject, Assignment, AssignmentSubmission, Grade 
from .models import Student
from accounts.models import CustomUser
from django.contrib import messages
from django.utils import timezone

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
    students = guardian.ward_students.all().select_related('user', 'current_class')
    
    # Calculate averages
    avg_attendance = round(sum(s.attendance_percentage for s in students) / len(students)) if students else 0
    
    # Get recent activities from multiple sources
    recent_activities = []
    
    # Get recent submissions (last 3 days)
    for student in students:
        submissions = AssignmentSubmission.objects.filter(
            student=student,
            submission_date__gte=timezone.now() - timezone.timedelta(days=3)
        ).select_related('assignment', 'assignment__subject').order_by('-submission_date')[:5]
        
        for submission in submissions:
            recent_activities.append({
                'activity_type': 'submission',
                'student': student,
                'assignment': submission.assignment,
                'timestamp': submission.submission_date,
                'grade': submission.grade,
                'is_late': submission.is_late
            })
    
    # Get recent grades (last week)
    for student in students:
        grades = Grade.objects.filter(
            student=student,
            date_recorded__gte=timezone.now() - timezone.timedelta(days=7)
        ).select_related('subject').order_by('-date_recorded')[:3]
        
        for grade in grades:
            recent_activities.append({
                'activity_type': 'grade',
                'student': student,
                'grade_value': grade.marks,
                'subject': grade.subject,
                'remarks': grade.remarks,
                'timestamp': grade.date_recorded
            })
    
    # Get recent attendance records (last week)
    for student in students:
        # Check if attendance app is available
        try:
            from attendance.models import Attendance
            attendance_records = Attendance.objects.filter(
                student=student,
                date__gte=timezone.now().date() - timezone.timedelta(days=7)
            ).order_by('-date')[:5]
            
            for record in attendance_records:
                recent_activities.append({
                    'activity_type': 'attendance',
                    'student': student,
                    'status': record.status,
                    'date': record.date,
                    'remarks': getattr(record, 'remarks', ''),
                    'timestamp': record.date  # Using date as timestamp
                })
        except ImportError:
            # Attendance app not available
            pass
    
    # Sort all activities by timestamp (most recent first)
    recent_activities.sort(key=lambda x: x['timestamp'], reverse=True)
    
    # Get the 10 most recent activities
    recent_activities = recent_activities[:10]
    
    # Get upcoming events (next 7 days) - assuming you have an Event model
    upcoming_events = []
    try:
        from events.models import Event
        upcoming_events = Event.objects.filter(
            event_date__gte=timezone.now().date(),
            event_date__lte=timezone.now().date() + timezone.timedelta(days=7)
        ).order_by('event_date')[:5]
    except ImportError:
        # Events model not available
        pass
    
    # Count pending assignments (due in future or past due but not submitted)
    pending_assignments = 0
    for student in students:
        if student.current_class:
            # Get assignments for the student's class that are due
            class_assignments = Assignment.objects.filter(
                class_assigned=student.current_class,
                due_date__gte=timezone.now() - timezone.timedelta(days=7)  # Include recently past due
            )
            
            for assignment in class_assignments:
                # Check if student has submitted this assignment
                if not AssignmentSubmission.objects.filter(
                    assignment=assignment, 
                    student=student
                ).exists():
                    pending_assignments += 1
    
    # Set new_notifications to 0 since we don't have notifications model
    new_notifications = 0
    
    context = {
        'guardian': guardian,
        'students': students,
        'recent_activities': recent_activities,
        'avg_attendance': avg_attendance,
        'pending_assignments': pending_assignments,
        'new_notifications': new_notifications,
        'upcoming_events': upcoming_events,
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
def guardian_student_grades(request, user_id):
    guardian = request.user.guardian_profile
    student = get_object_or_404(Student, user_id=user_id)
    
    # Verify the student is under this guardian's care
    if student.guardian != guardian:
        return HttpResponseForbidden("You don't have permission to view this student's grades")
    
    # Assuming Grade model exists with student ForeignKey
    grades = student.grades.select_related('subject').order_by('-date_recorded')
    
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
    student = get_object_or_404(Student, user_id=student_id)
    
    # Verify the student is under this guardian's care
    if student.guardian != guardian:
        return HttpResponseForbidden("You don't have permission to view this student's attendance")
    
    # Get attendance records - NOT using attendance_percentage
    try:
        from attendance.models import Attendance
        attendance_records = Attendance.objects.filter(student=student).order_by('-date')
        
        # Calculate attendance stats
        total_days = attendance_records.count()
        present_days = attendance_records.filter(status='Present').count()
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
        
    except ImportError:
        # Attendance app not available
        context = {
            'student': student,
            'error': 'Attendance tracking is not available at this time.'
        }
    
    return render(request, 'students/guardian_student_attendance.html', context)