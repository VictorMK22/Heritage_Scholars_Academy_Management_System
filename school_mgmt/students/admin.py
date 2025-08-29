from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils import timezone
from datetime import date
from .models import Guardian, Student
from accounts.models import CustomUser
from academics.models import Class
from django import forms
from django.shortcuts import render

class GuardianInline(admin.StackedInline):
    """Inline admin for Guardian model"""
    model = Guardian
    extra = 0
    fields = ('user', 'address', 'relationship_to_student')
    readonly_fields = ('user',)

class StudentInline(admin.StackedInline):
    """Inline admin for Student model"""
    model = Student
    extra = 0
    fields = ('admission_number','current_class', 'date_of_birth', 'guardian') 
    readonly_fields = ('admission_number',)
    show_change_link = True

@admin.register(Guardian)
class GuardianAdmin(admin.ModelAdmin):
    list_display = ('user', 'relationship_to_student', 'address', 'student_count')
    list_filter = ('relationship_to_student',)
    search_fields = ('user__first_name', 'user__last_name', 'user__email')
    raw_id_fields = ('user',)
    inlines = [StudentInline]
    
    def student_count(self, obj):
        count = obj.ward_students.count()
        url = reverse('admin:students_student_changelist') + f'?guardian__id__exact={obj.id}'
        return format_html('<a href="{}">{} Student(s)</a>', url, count)
    student_count.short_description = 'Students'

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        'admission_number', 
        'user_link', 
        'current_class_link', 
        'display_age',
        'guardian_link', 
        'status_badge',
        'attendance_display'
    )
    list_filter = (
        'current_class', 
        'user__is_active',
    )
    search_fields = (
        'admission_number', 
        'user__first_name', 
        'user__last_name',
        'guardian__user__first_name', 
        'guardian__user__last_name'
    )
    raw_id_fields = ('user', 'guardian')
    readonly_fields = ('display_age', 'attendance_display', 'gpa_display')
    actions = ['activate_students', 'deactivate_students']
    
    fieldsets = (
        ('Personal Information', {
            'fields': (
                'user', 
                'admission_number', 
                'date_of_birth', 
                'display_age'
            )
        }),
        ('Academic Information', {
            'fields': (
                'current_class',
                'gpa_display',
                'attendance_display'
            )
        }),
        ('Guardian Information', {
            'fields': ('guardian',),
            'classes': ('collapse',)
        }),
    )

    actions = ['assign_to_class', 'assign_to_guardian', 'activate_students', 'deactivate_students']

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        
        # Add class assignment to academic information
        academic_fields = list(fieldsets[1][1]['fields'])
        if 'current_class' not in academic_fields:
            academic_fields.insert(0, 'current_class')
            fieldsets[1][1]['fields'] = tuple(academic_fields)
            
        return fieldsets
    
    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj)
        if obj:  # editing existing object
            return readonly_fields + ('admission_number',)
        return readonly_fields
    
    def user_link(self, obj):
        url = reverse('admin:accounts_customuser_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.get_full_name())
    user_link.short_description = 'Student'
    user_link.admin_order_field = 'user__last_name'

    def current_class_link(self, obj):
        if obj.current_class:
            url = reverse('admin:academics_class_change', args=[obj.current_class.id])
            return format_html('<a href="{}">{}</a>', url, obj.current_class)
        return "-"
    current_class_link.short_description = 'Class'

    def guardian_link(self, obj):
        if obj.guardian:
            url = reverse('admin:students_guardian_change', args=[obj.guardian.id])
            return format_html('<a href="{}">{} ({})</a>', url, 
                            obj.guardian.user.get_full_name(), 
                            obj.guardian.relationship_to_student)
        return "-"
    guardian_link.short_description = 'Guardian'

    def status_badge(self, obj):
        color = 'success' if obj.user.is_active else 'secondary'
        text = 'Active' if obj.user.is_active else 'Inactive'
        return format_html(
            '<span class="badge bg-{}">{}</span>', 
            color, 
            text
        )
    status_badge.short_description = 'Status'

    def assign_to_guardian(self, request, queryset):
        # Check if this is the form submission
        if 'apply' in request.POST:  # Check for the submit button name
            guardian_id = request.POST.get("guardian")
            print(f"DEBUG: Form submitted with guardian ID: {guardian_id}")
            
            if not guardian_id:
                self.message_user(request, "Please select a guardian", level='error')
            else:
                try:
                    guardian_obj = Guardian.objects.get(pk=guardian_id)
                    updated = queryset.update(guardian=guardian_obj)
                    self.message_user(request, f"Successfully assigned {updated} students to {guardian_obj.user.get_full_name()}")
                    return None  # Return to changelist
                except Guardian.DoesNotExist:
                    self.message_user(request, "Selected guardian does not exist", level='error')
        
        # Show the form (GET request or form with errors)
        guardians = Guardian.objects.select_related('user').all()
        return render(request, "admin/students/student/bulk_assign_guardian.html", {
            "students": queryset,
            "guardians": guardians,
            "title": "Assign Guardian to Selected Students",
        })
    assign_to_guardian.short_description = "Assign selected students to a guardian"


    def display_age(self, obj):
        try:
            return obj.age() or "-"
        except Exception:
            return "-"
    display_age.short_description = "Age"


    def attendance_display(self, obj):
        percentage = obj.attendance_percentage
        color = 'success' if percentage >= 75 else 'warning' if percentage >= 50 else 'danger'
        return format_html(
            '<span class="badge bg-{}">{}%</span>', 
            color, 
            percentage
        )
    attendance_display.short_description = 'Attendance'

    def gpa_display(self, obj):
        gpa = obj.get_gpa()
        if gpa is None:
            return "-"
        color = 'success' if gpa >= 3.0 else 'warning' if gpa >= 2.0 else 'danger'
        return format_html(
            '<span class="badge bg-{}">{:.2f}</span>', 
            color, 
            gpa
        )
    gpa_display.short_description = 'GPA'

    def activate_students(self, request, queryset):
        updated = queryset.update(user__is_active=True)
        self.message_user(request, f"Activated {updated} students")
    activate_students.short_description = "Activate selected students"

    def deactivate_students(self, request, queryset):
        updated = queryset.update(user__is_active=False)
        self.message_user(request, f"Deactivated {updated} students")
    deactivate_students.short_description = "Deactivate selected students"

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj)
        if obj:  # editing existing object
            return readonly_fields + ('admission_number',)
        return readonly_fields

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'user', 
            'current_class', 
            'guardian', 
            'guardian__user'
        )

    def assign_to_class(self, request, queryset):
        if 'apply' in request.POST:
            class_id = request.POST['class']
            class_obj = Class.objects.get(pk=class_id)
            updated = queryset.update(current_class=class_obj)
            self.message_user(request, f"Successfully assigned {updated} students to {class_obj.name}")
            return
        
        classes = Class.objects.all()
        return render(request, 'admin/students/student/assign_students_to_class.html', {
            'students': queryset,
            'classes': classes,
        })
    
    assign_to_class.short_description = "Assign selected students to class"

    class Media:
        css = {
            'all': (
                'css/base.css',
            )
        }