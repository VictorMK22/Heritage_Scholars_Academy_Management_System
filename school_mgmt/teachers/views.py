from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Teacher
from academics.models import Class, Subject, Assignment, AssignmentSubmission
from students.models import Student
from attendance.models import Attendance
from django.utils import timezone
from academics.utils import current_academic_year

@login_required
def dashboard(request):
    try:
        # Get teacher with related user data
        teacher = Teacher.objects.select_related('user').get(user=request.user)
    except Teacher.DoesNotExist:
        messages.error(request, "You are not registered as a teacher.")
        return redirect('accounts:profile')

    current_year = current_academic_year()
    
    # Get current teaching assignments with subjects
    current_assignments = teacher.currently_teaching()
    
    # CONSISTENT FILTERING: Apply academic year filter to ALL assignment queries
    assignment_filter = {
        'teacher': teacher,
        'subject__academic_year': current_year
    }
    
    # Get recent assignments with consistent filtering
    recent_assignments = Assignment.objects.filter(
        **assignment_filter
    ).select_related('subject', 'class_assigned').order_by('-date_created')[:5]
    
    # Calculate statistics with consistent filtering
    assignment_count = Assignment.objects.filter(**assignment_filter).count()
    
    upcoming_assignments = Assignment.objects.filter(
        **assignment_filter,
        due_date__gte=timezone.now()
    ).order_by('due_date')[:3]
    
    # Initialize variables for class teacher specific data
    recent_attendance = None
    primary_class = None
    student_count = 0
    
    # IMPROVED ERROR HANDLING for class teachers
    if teacher.is_class_teacher:
        # Check if teacher actually has current assignments
        if current_assignments.exists():
            # Get the primary class assignment if exists
            primary_assignment = current_assignments.filter(is_primary=True).first()
            if primary_assignment:
                primary_class = primary_assignment.classroom
                try:
                    student_count = primary_class.student_set.count()
                except AttributeError:
                    student_count = 0
                    
                # Get recent attendance records
                recent_attendance = Attendance.objects.filter(
                    recorded_by=teacher,
                    date__gte=timezone.now() - timezone.timedelta(days=7)
                ).select_related('student', 'student__current_class').order_by('-date')[:5]
        else:
            # Teacher is marked as class teacher but has no current assignments
            messages.warning(
                request, 
                "You are marked as a class teacher but have no classes assigned for the current academic year. "
                "Please contact the administration to resolve this."
            )
    
    context = {
        'teacher': teacher,
        'current_assignments': current_assignments,
        'recent_assignments': recent_assignments,
        'recent_attendance': recent_attendance,
        'primary_class': primary_class,
        'student_count': student_count,
        'current_academic_year': current_year,
        'assignment_count': assignment_count,
        'upcoming_assignments': upcoming_assignments,
        'is_class_teacher': teacher.is_class_teacher,
        'has_current_assignments': current_assignments.exists(),  # New flag
    }
    
    return render(request, 'teachers/dashboard.html', context)


@login_required
def activity_log(request):
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        messages.error(request, "You are not registered as a teacher.")
        return redirect('accounts:profile')
    
    current_year = current_academic_year()
    
    # CONSISTENT FILTERING: Apply academic year filter here too
    assignments = Assignment.objects.filter(
        teacher=teacher,
        subject__academic_year=current_year  # Added academic year filter
    ).select_related('subject', 'class_assigned').order_by('-date_created')[:50]
    
    # Initialize attendance records
    attendances = []
    
    # IMPROVED ERROR HANDLING for class teachers
    if teacher.is_class_teacher:
        current_assignments = teacher.currently_teaching()
        if current_assignments.exists():
            # Get the primary class assignment if exists
            primary_assignment = current_assignments.filter(is_primary=True).first()
            if primary_assignment:
                try:
                    attendances = Attendance.objects.filter(
                        student__current_class=primary_assignment.classroom
                    ).select_related('student', 'student__current_class').order_by('-date')[:50]
                except Exception as e:
                    # Log the error but don't break the view
                    attendances = []
                    messages.warning(request, "Unable to load attendance records.")
        else:
            messages.info(
                request, 
                "No attendance records available - you don't have any classes assigned for the current academic year."
            )
    
    context = {
        'assignments': assignments,
        'attendances': attendances,
        'teacher': teacher,
        'is_class_teacher': teacher.is_class_teacher,
        'current_academic_year': current_year,  # Added for template use
        'has_assignments': assignments.exists(),  # New flag
        'has_attendances': len(attendances) > 0,  # New flag
    }
    
    return render(request, 'teachers/activity_log.html', context)


@login_required
def class_list(request):
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        messages.error(request, "You are not registered as a teacher.")
        return redirect('accounts:profile')
    
    classes_taught = Class.objects.filter(subjects__teacher=teacher).distinct()
    
    context = {
        'classes': classes_taught,
        'is_class_teacher': teacher.is_class_teacher,
    }
    return render(request, 'teachers/class_list.html', context)

@login_required 
def create_assignment(request):
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        messages.error(request, "You are not registered as a teacher.")
        return redirect('accounts:profile')
    
    # ERROR HANDLING: Check if teacher has current assignments
    current_assignments = teacher.currently_teaching()
    if not current_assignments.exists():
        messages.error(
            request, 
            "You don't have any classes assigned for the current academic year. "
            "Cannot create assignments without class assignments."
        )
        return redirect('teachers:dashboard')
    
    if request.method == 'POST':
        try:
            # Get form data
            title = request.POST.get('title')
            description = request.POST.get('description')
            subject_id = request.POST.get('subject')
            due_date = request.POST.get('due_date')
            points = request.POST.get('points', 100)
            is_published = 'is_published' in request.POST
            
            # Validate required fields
            if not all([title, description, subject_id, due_date]):
                raise ValueError("All required fields must be filled")
            
            # Get subject and class with error handling
            try:
                subject = Subject.objects.get(id=subject_id)
            except Subject.DoesNotExist:
                raise ValueError("Invalid subject selected")
                
            # Find class assignment for this subject
            class_teaching = current_assignments.filter(subjects=subject).first()
            if not class_teaching:
                raise ValueError("You are not assigned to teach this subject")
                
            class_assigned = class_teaching.classroom
            
            # Create assignment
            assignment = Assignment.objects.create(
                title=title,
                description=description,
                subject=subject,
                class_assigned=class_assigned,
                teacher=teacher,
                due_date=due_date,
                points=points,
                is_published=is_published
            )
            
            # Handle file upload
            if 'attachment' in request.FILES:
                assignment.attachment = request.FILES['attachment']
                assignment.save()
            
            messages.success(request, "Assignment created successfully!")
            return redirect('teachers:dashboard')
            
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f"Error creating assignment: {str(e)}")
    
    # CONSISTENT FILTERING: Get subjects with academic year filter
    current_year = current_academic_year()
    subjects = Subject.objects.filter(
        id__in=current_assignments.values_list('subjects__id', flat=True),
        academic_year=current_year
    ).distinct()
    
    # ERROR HANDLING: Check if teacher has subjects to teach
    if not subjects.exists():
        messages.warning(
            request,
            "No subjects available for assignment creation. "
            "Please ensure you have subjects assigned for the current academic year."
        )
    
    context = {
        'subjects': subjects,
        'min_date': timezone.now().strftime('%Y-%m-%dT%H:%M'),
        'has_subjects': subjects.exists(),  # New flag for template
    }
    return render(request, 'teachers/create_assignment.html', context)


@login_required
def grade_submissions(request):
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        messages.error(request, "You are not registered as a teacher.")
        return redirect('accounts:profile')
    
    assignments = Assignment.objects.filter(teacher=teacher)
    submissions = AssignmentSubmission.objects.filter(
        assignment__in=assignments
    ).select_related('student', 'assignment')
    
    if request.method == 'POST':
        submission_id = request.POST.get('submission_id')
        grade = request.POST.get('grade')
        feedback = request.POST.get('feedback', '')
        
        submission = get_object_or_404(AssignmentSubmission, id=submission_id)
        if grade:  # Only update grade if a value was provided
            submission.grade = grade
        submission.feedback = feedback
        submission.save()
        messages.success(request, "Submission graded successfully!")
        return redirect('teachers:grade_submissions')
    
    # Filter ungraded submissions (where grade is None)
    ungraded_submissions = submissions.filter(grade__isnull=True)
    
    # Filter graded submissions (where grade is not None)
    graded_submissions = submissions.exclude(grade__isnull=True)
    
    context = {
        'submissions': submissions,
        'ungraded_submissions': ungraded_submissions,
        'graded_submissions': graded_submissions,
    }
    return render(request, 'teachers/grade_submissions.html', context)

@login_required
def take_attendance(request):
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        messages.error(request, "You are not registered as a teacher.")
        return redirect('accounts:profile')

    # Check if teacher is a class teacher
    if not teacher.is_class_teacher:
        messages.error(request, "Only class teachers can take attendance.")
        return redirect('teachers:dashboard')

    # Get the primary class this teacher teaches
    primary_class = Class.objects.filter(
        teaching_assignments__teacher=teacher,
        teaching_assignments__is_primary=True
    ).first()

    if not primary_class:
        messages.error(request, "You are not assigned as a primary teacher for any class.")
        return redirect('teachers:dashboard')

    students = Student.objects.filter(current_class=primary_class)

    if request.method == 'POST':
        date = request.POST.get('date', timezone.now().date())
        attendance_data = request.POST.getlist('attendance')

        for student in students:
            status = str(student.id) in attendance_data
            Attendance.objects.create(
                student=student,
                date=date,
                status='Present' if status else 'Absent'
            )
        messages.success(request, "Attendance recorded successfully!")
        return redirect('teachers:dashboard')

    context = {
        'students': students,
        'class': primary_class,
        'today': timezone.now().strftime('%Y-%m-%d'),
    }
    return render(request, 'teachers/take_attendance.html', context)