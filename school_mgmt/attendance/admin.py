from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Attendance

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student_link', 'formatted_date', 'status', 'actions_column')
    list_filter = ('status', 'date')
    search_fields = ('student__user__first_name', 'student__user__last_name', 'student__admission_number')
    date_hierarchy = 'date'
    list_per_page = 20
    ordering = ('-date',)
    
    fields = ('student', 'date', 'status')
    
    def student_link(self, obj):
        # Check if student exists and has an id
        if obj.student and obj.student.pk:
            url = reverse('admin:students_student_change', args=[obj.student.pk])
            return format_html('<a href="{}">{}</a>', url, obj.student)
        else:
            return "No student linked"
    student_link.short_description = 'Student'
    student_link.admin_order_field = 'student__user__first_name'
    
    def formatted_date(self, obj):
        return obj.date.strftime('%Y-%m-%d %H:%M')
    formatted_date.short_description = 'Date'
    formatted_date.admin_order_field = 'date'
    
    def actions_column(self, obj):
        return format_html(
            '<a class="button" href="{}">Edit</a>&nbsp;'
            '<a class="button" href="{}">Delete</a>',
            reverse('admin:attendance_attendance_change', args=[obj.id]),
            reverse('admin:attendance_attendance_delete', args=[obj.id])
        )
    actions_column.short_description = 'Actions'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('student__user')