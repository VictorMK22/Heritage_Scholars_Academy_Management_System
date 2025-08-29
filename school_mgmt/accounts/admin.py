from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from django.utils.translation import gettext_lazy as _

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'get_full_name', 'role', 'is_verified', 'is_active')
    list_filter = ('role', 'is_verified', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal Info'), {
            'fields': (
                'first_name', 
                'last_name', 
                'email', 
                'phone',
                'date_of_birth',
                'address',
                'profile_picture'
            )
        }),
        (_('Roles and Permissions'), {
            'fields': (
                'role',
                'is_verified',
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions'
            )
        }),
        (_('Important Dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username',
                'email',
                'password1',
                'password2',
                'role',
                'is_verified'
            ),
        }),
    )
    
    # Make the methods available in list display
    @admin.display(description='Full Name')
    def get_full_name(self, obj):
        return obj.get_full_name()

admin.site.register(CustomUser, CustomUserAdmin)