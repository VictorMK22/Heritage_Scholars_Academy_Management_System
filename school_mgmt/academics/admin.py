from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from teachers.models import Teacher
from .models import Class, ClassTeaching, Subject, Grade, Assignment, AssignmentSubmission 

class ClassTeachingInline(admin.TabularInline):
    model = ClassTeaching
    extra = 1
    raw_id_fields = ('teacher',)
    autocomplete_fields = ['subjects']
    fields = ('teacher', 'is_primary', 'subjects', 'date_assigned')
    readonly_fields = ('date_assigned',)

@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'teacher_list', 'student_count', 'primary_teacher_display')
    search_fields = ('name',)
    list_filter = ('teachers',)
    inlines = [ClassTeachingInline]
    
    def teacher_list(self, obj):
        teachers = obj.teachers.all()
        if not teachers:
            return "-"
        return format_html(", ".join([
            f'<a href="{reverse("admin:teachers_teacher_change", args=[t.id])}">{t.user.get_full_name()}</a>'
            for t in teachers
        ]))
    teacher_list.short_description = 'Teachers'
    
    def student_count(self, obj):
        count = obj.student_set.count()  # Using default related_name
        url = reverse('admin:students_student_changelist') + f'?current_class__id__exact={obj.id}'
        return format_html('<a href="{}">{} Student{}</a>', url, count, "s" if count != 1 else "")
    student_count.short_description = 'Students'
    
    def primary_teacher_display(self, obj):
        primary = obj.get_primary_teacher()
        if primary:
            url = reverse("admin:teachers_teacher_change", args=[primary.teacher.id])
            return format_html('<a href="{}">{}</a>', url, primary.teacher.user.get_full_name())
        return "-"
    primary_teacher_display.short_description = 'Primary Teacher'

@admin.register(ClassTeaching)
class ClassTeachingAdmin(admin.ModelAdmin):
    list_display = ('classroom', 'teacher_link', 'is_primary', 'subjects_list')
    list_filter = ('is_primary', 'classroom')
    search_fields = ('classroom__name', 'teacher__user__first_name', 'teacher__user__last_name')
    filter_horizontal = ('subjects',)
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Ensure we're using the correct teacher queryset
        if 'teacher' in form.base_fields:
            form.base_fields['teacher'].queryset = Teacher.objects.all().select_related('user')
            form.base_fields['teacher'].label_from_instance = lambda obj: f"{obj.user.get_full_name()} ({obj.employee_id})"
        return form
    
    def teacher_link(self, obj):
        if obj.teacher_id:
            url = reverse('admin:teachers_teacher_change', args=[obj.teacher.id])
            return format_html('<a href="{}">{}</a>', url, obj.teacher.user.get_full_name())
        return "Not assigned"
    teacher_link.short_description = 'Teacher'
    
    def subjects_list(self, obj):
        return ", ".join([s.name for s in obj.subjects.all()])
    subjects_list.short_description = 'Subjects'

class SubjectInline(admin.TabularInline):
    model = Subject
    extra = 1
    fields = ('name', 'term', 'teacher')
    raw_id_fields = ('teacher',)

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'class_assigned_link', 'teacher_link', 'term')
    list_filter = ('class_assigned', 'term')
    search_fields = ('name', 'class_assigned__name')
    raw_id_fields = ('teacher', 'class_assigned')
    
    def class_assigned_link(self, obj):
        url = reverse('admin:academics_class_change', args=[obj.class_assigned.id])
        return format_html('<a href="{}">{}</a>', url, obj.class_assigned)
    class_assigned_link.short_description = 'Class'
    
    def teacher_link(self, obj):
        if obj.teacher:
            url = reverse('admin:teachers_teacher_change', args=[obj.teacher.id])
            return format_html('<a href="{}">{}</a>', url, obj.teacher.user.get_full_name())
        return "-"
    teacher_link.short_description = 'Teacher'

class GradeInline(admin.TabularInline):
    model = Grade
    extra = 0
    fields = ('subject', 'marks', 'date_recorded', 'remarks')
    readonly_fields = ('date_recorded',)
    raw_id_fields = ('subject',)

@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ('student_link', 'subject_link', 'marks', 'date_recorded')
    list_filter = ('subject__class_assigned', 'subject')
    search_fields = ('student__user__first_name', 'student__user__last_name', 'subject__name')
    raw_id_fields = ('student', 'subject')
    
    def student_link(self, obj):
        url = reverse('admin:students_student_change', args=[obj.student.id])
        return format_html('<a href="{}">{}</a>', url, obj.student.user.get_full_name())
    student_link.short_description = 'Student'
    
    def subject_link(self, obj):
        url = reverse('admin:academics_subject_change', args=[obj.subject.id])
        return format_html('<a href="{}">{}</a>', url, obj.subject)
    subject_link.short_description = 'Subject'

class AssignmentSubmissionInline(admin.TabularInline):
    model = AssignmentSubmission
    extra = 0
    fields = ('student_link', 'submitted_file', 'grade', 'is_late')
    readonly_fields = ('student_link', 'is_late')
    
    def student_link(self, obj):
        url = reverse('admin:students_student_change', args=[obj.student.id])
        return format_html('<a href="{}">{}</a>', url, obj.student.user.get_full_name())
    student_link.short_description = 'Student'

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject_link', 'class_assigned_link', 'due_date', 'is_published', 'is_past_due')
    list_filter = ('is_published', 'class_assigned', 'subject')
    search_fields = ('title', 'description', 'subject__name')
    raw_id_fields = ('teacher', 'subject', 'class_assigned')
    inlines = [AssignmentSubmissionInline]
    date_hierarchy = 'due_date'
    
    def subject_link(self, obj):
        url = reverse('admin:academics_subject_change', args=[obj.subject.id])
        return format_html('<a href="{}">{}</a>', url, obj.subject)
    subject_link.short_description = 'Subject'
    
    def class_assigned_link(self, obj):
        url = reverse('admin:academics_class_change', args=[obj.class_assigned.id])
        return format_html('<a href="{}">{}</a>', url, obj.class_assigned)
    class_assigned_link.short_description = 'Class'

@admin.register(AssignmentSubmission)
class AssignmentSubmissionAdmin(admin.ModelAdmin):
    list_display = ('assignment_link', 'student_link', 'submission_date', 'grade', 'is_late')
    list_filter = ('is_late', 'assignment__class_assigned')
    search_fields = ('student__user__first_name', 'student__user__last_name', 'assignment__title')
    raw_id_fields = ('student', 'assignment')
    readonly_fields = ('is_late',)
    
    def assignment_link(self, obj):
        url = reverse('admin:academics_assignment_change', args=[obj.assignment.id])
        return format_html('<a href="{}">{}</a>', url, obj.assignment)
    assignment_link.short_description = 'Assignment'
    
    def student_link(self, obj):
        url = reverse('admin:students_student_change', args=[obj.student.id])
        return format_html('<a href="{}">{}</a>', url, obj.student.user.get_full_name())
    student_link.short_description = 'Student'