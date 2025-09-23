from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    # Student routes
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    path('subjects/', views.student_subject_list, name='student_subject_list'),
    path('assignments/', views.student_assignment_list, name='student_assignment_list'),

    path('admin/assign-to-class/', views.assign_students_to_class, name='assign_to_class'),
    
    # Guardian routes
    path('guardian/dashboard/', views.guardian_dashboard, name='guardian_dashboard'),
    path('guardian/my-students/', views.guardian_student_list, name='guardian_student_list'),
    path('guardian/my-students/classes/', views.guardian_student_classes, name='guardian_student_classes'),
    path('guardian/student/<int:user_id>/grades/', views.guardian_student_grades, name='guardian_student_grades'),
    path('guardian/student/<int:student_id>/attendance/', views.guardian_student_attendance, name='guardian_student_attendance'),
]