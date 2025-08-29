from django.urls import path
from .views import (
    AttendanceListView,
    take_attendance,
    AttendanceUpdateView,
    AttendanceDeleteView
)

app_name = 'attendance'

urlpatterns = [
    path('', AttendanceListView.as_view(), name='list'),
    path('take/', take_attendance, name='take'),
    path('<int:pk>/edit/', AttendanceUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', AttendanceDeleteView.as_view(), name='delete'),
]