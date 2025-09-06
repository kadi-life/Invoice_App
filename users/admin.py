from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.contrib import messages
from .models import CustomUser
from django.shortcuts import redirect
from django.contrib.admin import AdminSite

class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'role', 'is_staff', 'is_superuser', 'is_active', 'date_joined')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'role', 'profile_picture')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'role', 'password1', 'password2'),
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Regular staff users can only see their own profile
        return qs.filter(id=request.user.id)
    
    def get_list_display(self, request):
        if request.user.is_superuser:
            return self.list_display
        # Regular staff users see limited info
        return ('email', 'first_name', 'last_name', 'role', 'is_active', 'date_joined')
    
    def has_add_permission(self, request):
        # Only superusers can add users through Django admin
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        # Regular staff users can only edit their own profile
        return obj is not None and obj.id == request.user.id
    
    def has_delete_permission(self, request, obj=None):
        # Only superusers can delete users
        return request.user.is_superuser
    
    def has_view_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        # Regular staff users can only view their own profile
        return obj is not None and obj.id == request.user.id

admin.site.register(CustomUser, CustomUserAdmin)

# Add a custom admin site title and header
admin.site.site_header = "Invoice System Administration"
admin.site.site_title = "Invoice System Admin"
admin.site.index_title = "Welcome to Invoice System Administration"
