from django.contrib import admin
from .models import Fee
from students.models import Student
from django.utils.html import format_html

class FeeInline(admin.TabularInline):
    model = Fee
    extra = 0
    fields = ('amount', 'status', 'due_date')
    readonly_fields = ('status',)

@admin.register(Fee)
class FeeAdmin(admin.ModelAdmin):
    list_display = ('student', 'amount', 'status', 'due_date')
    list_filter = ('status', 'due_date')
    search_fields = ('student__user__first_name', 'student__user__last_name')

# Extend Student admin with fee information
from students.admin import StudentAdmin as BaseStudentAdmin

BaseStudentAdmin.inlines = [FeeInline] + list(BaseStudentAdmin.inlines or [])
BaseStudentAdmin.list_display += ('fee_status',)

def fee_status(self, obj):
    from .models import Fee
    unpaid = Fee.objects.filter(student=obj, status='Unpaid').exists()
    return format_html(
        '<span style="color: {};">{}</span>',
        'red' if unpaid else 'green',
        'Unpaid' if unpaid else 'Paid'
    )
fee_status.short_description = 'Fee Status'
BaseStudentAdmin.fee_status = fee_status