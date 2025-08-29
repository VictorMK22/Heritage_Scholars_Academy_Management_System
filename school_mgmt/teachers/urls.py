# teachers/urls.py
from django.urls import path
from . import views

app_name = 'teachers'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('activity-log/', views.activity_log, name='activity_log'),
    path('my-classes/', views.class_list, name='class_list'),
    path('create-assignment/', views.create_assignment, name='create_assignment'),
    path('grade-submissions/', views.grade_submissions, name='grade_submissions'),
    path('take-attendance/', views.take_attendance, name='take_attendance'),
]