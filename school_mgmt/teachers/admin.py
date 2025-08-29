from django.contrib import admin
from .models import Teacher
from accounts.models import CustomUser
from accounts.admin import CustomUserAdmin

class TeacherInline(admin.StackedInline):
    model = Teacher
    can_delete = False
    verbose_name_plural = 'Teacher Profile'
    fields = (
        'employee_id',
        'specialization',
        'qualification',
        'is_class_teacher',
        'profile_picture',
        'bio'
    )
    readonly_fields = ('joining_date',)
    fk_name = 'user'
    extra = 0

# Get the existing admin class safely
try:
    existing_admin = admin.site._registry[CustomUser].__class__
    # Create new admin class that inherits from existing
    class ExtendedCustomUserAdmin(existing_admin):
        inlines = list(getattr(existing_admin, 'inlines', [])) + [TeacherInline]
    
    # Unregister and re-register
    admin.site.unregister(CustomUser)
    admin.site.register(CustomUser, ExtendedCustomUserAdmin)
except KeyError:
    # If CustomUser isn't registered yet (shouldn't happen if accounts loads first)
    class ExtendedCustomUserAdmin(CustomUserAdmin):
        inlines = [TeacherInline]
    admin.site.register(CustomUser, ExtendedCustomUserAdmin)

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = (
        'get_user_full_name',
        'employee_id',
        'specialization',
        'is_class_teacher',
        'get_user_email'
    )
    list_filter = ('is_class_teacher', 'specialization')
    search_fields = (
        'user__first_name',
        'user__last_name',
        'employee_id',
        'user__email'
    )
    readonly_fields = ('joining_date', 'get_current_subjects')
    raw_id_fields = ('user',)
    
    fieldsets = (
        (None, {'fields': ('user', 'employee_id')}),
        ('Professional Info', {
            'fields': ('specialization', 'qualification', 'is_class_teacher')
        }),
        ('Profile', {
            'fields': ('profile_picture', 'bio'),
            'classes': ('collapse',)
        }),
        ('Timeline', {
            'fields': ('joining_date',),
            'classes': ('collapse',)
        }),
    )

    def get_user_full_name(self, obj):
        return obj.user.get_full_name()
    get_user_full_name.short_description = 'Name'
    get_user_full_name.admin_order_field = 'user__last_name'

    def get_user_email(self, obj):
        return obj.user.email
    get_user_email.short_description = 'Email'
    get_user_email.admin_order_field = 'user__email'

    def get_current_subjects(self, obj):
        from academics.models import Subject
        current_year = f"{timezone.now().year}-{timezone.now().year+1}"
        subjects = Subject.objects.filter(teacher=obj, academic_year=current_year)
        if subjects.exists():
            return ", ".join([s.name for s in subjects])
        return "No current teaching assignments"
    get_current_subjects.short_description = 'Currently Teaching'