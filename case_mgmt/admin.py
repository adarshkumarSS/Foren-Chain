# case_mgmt/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'is_ipfs_connected')
    list_filter = ('role', 'is_ipfs_connected')
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('role', 'pinata_api_key', 'pinata_secret', 'is_ipfs_connected')}),
    )

class CaseAdmin(admin.ModelAdmin):
    list_display = ('name', 'case_number', 'case_type', 'status', 'created_by', 'created_at')
    list_filter = ('case_type', 'status')
    search_fields = ('name', 'case_number', 'description')

class CaseFileAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'case', 'file_type', 'uploaded_at')
    list_filter = ('file_type',)
    search_fields = ('file_name', 'cid')

class DisclosureFormAdmin(admin.ModelAdmin):
    list_display = ('form_name', 'case', 'added_by', 'added_at')
    search_fields = ('form_name', 'form_pdf_cid')

class CaseActivityLogAdmin(admin.ModelAdmin):
    list_display = ('case', 'user', 'activity', 'timestamp')
    list_filter = ('user',)
    search_fields = ('activity',)

class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'case', 'message', 'is_read', 'created_at')
    list_filter = ('is_read', 'user')
    search_fields = ('message',)

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Case, CaseAdmin)
admin.site.register(CaseFile, CaseFileAdmin)
admin.site.register(DisclosureForm, DisclosureFormAdmin)
admin.site.register(CaseActivityLog, CaseActivityLogAdmin)
admin.site.register(Notification, NotificationAdmin)
admin.site.register(UserRecentCase)