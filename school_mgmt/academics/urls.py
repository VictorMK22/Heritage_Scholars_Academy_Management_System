from django.urls import path
from . import views

app_name = 'academics'

urlpatterns = [
    # Class URLs
    path('classes/', views.ClassListView.as_view(), name='class_list'),
    path('classes/create/', views.ClassCreateView.as_view(), name='class_create'),
    path('classes/<int:pk>/', views.ClassDetailView.as_view(), name='class_detail'),
    path('classes/<int:pk>/assign-teachers/', views.ClassAssignTeachersView.as_view(), name='class_assign_teachers'),
    path('classes/<int:pk>/assign-subjects/', views.ClassAssignSubjectsView.as_view(), name='class_assign_subjects'),
    path('classes/<int:pk>/update/', views.ClassUpdateView.as_view(), name='class_update'),
    path('classes/<int:pk>/delete/', views.ClassDeleteView.as_view(), name='class_delete'),
    
    # Subject URLs
    path('subjects/', views.SubjectListView.as_view(), name='subject_list'),
    path('subjects/create/', views.SubjectCreateView.as_view(), name='subject_create'),
    path('subjects/<int:pk>/', views.SubjectDetailView.as_view(), name='subject_detail'),
    path('subjects/<int:pk>/update/', views.SubjectUpdateView.as_view(), name='subject_update'),
    path('subjects/<int:pk>/delete/', views.SubjectDeleteView.as_view(), name='subject_delete'),
    
    # Assignment URLs
    path('assignments/', views.AssignmentListView.as_view(), name='assignment_list'),
    path('assignments/create/', views.AssignmentCreateView.as_view(), name='assignment_create'),
    path('assignments/<int:pk>/', views.AssignmentDetailView.as_view(), name='assignment_detail'),
    path('assignments/<int:pk>/update/', views.AssignmentUpdateView.as_view(), name='assignment_update'),
    path('assignments/<int:pk>/delete/', views.AssignmentDeleteView.as_view(), name='assignment_delete'),
    
    # Assignment Submission URLs
    path('submissions/', views.SubmissionListView.as_view(), name='submission_list'),
    path('assignments/<int:assignment_id>/submit/', views.SubmissionCreateView.as_view(), name='submission_create'),
    path('submissions/<int:pk>/', views.SubmissionDetailView.as_view(), name='submission_detail'),
    path('submissions/<int:pk>/update/', views.SubmissionUpdateView.as_view(), name='submission_update'),
    path('submissions/<int:pk>/delete/', views.SubmissionDeleteView.as_view(), name='submission_delete'),
    path('submissions/<int:pk>/grade/', views.SubmissionGradeView.as_view(), name='submission_grade'),
    
    # Grade URLs
    path('grades/', views.GradeListView.as_view(), name='grade_list'),
    path('grades/create/', views.GradeCreateView.as_view(), name='grade_create'),
    path('grades/<int:pk>/', views.GradeDetailView.as_view(), name='grade_detail'),
    path('grades/<int:pk>/update/', views.GradeUpdateView.as_view(), name='grade_update'),
    path('grades/<int:pk>/delete/', views.GradeDeleteView.as_view(), name='grade_delete'),
    
    # Class-specific URLs
    path('classes/<int:class_id>/subjects/', views.ClassSubjectListView.as_view(), name='class_subject_list'),
    path('classes/<int:class_id>/assignments/', views.ClassAssignmentListView.as_view(), name='class_assignment_list'),
    path('classes/<int:class_id>/grades/', views.ClassGradeListView.as_view(), name='class_grade_list'),
    
    # Student-specific URLs
    path('students/<int:student_id>/grades/', views.StudentGradeListView.as_view(), name='student_grade_list'),
    path('students/<int:student_id>/assignments/', views.StudentAssignmentListView.as_view(), name='student_assignment_list'),
    path('students/<int:student_id>/submissions/', views.StudentSubmissionListView.as_view(), name='student_submission_list'),
    
    # Teacher-specific URLs
    path('teachers/<int:teacher_id>/classes/', views.TeacherClassListView.as_view(), name='teacher_class_list'),
    path('teachers/<int:teacher_id>/assignments/', views.TeacherAssignmentListView.as_view(), name='teacher_assignment_list'),
    
    # API endpoints
    path('api/classes/', views.ClassListAPI.as_view(), name='api_class_list'),
    path('api/classes/<int:pk>/', views.ClassDetailAPI.as_view(), name='api_class_detail'),
    path('api/assignments/', views.AssignmentListAPI.as_view(), name='api_assignment_list'),
    path('api/assignments/<int:pk>/', views.AssignmentDetailAPI.as_view(), name='api_assignment_detail'),
]