# case_mgmt/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class CustomUser(AbstractUser):
    ROLES = (
        ('forensic', 'Forensic'),
        ('police', 'Police'),
        ('lawyer', 'Lawyer'),
        ('court', 'Court'),
    )
    role = models.CharField(max_length=10, choices=ROLES)
    email = models.EmailField(unique=True)
    pinata_api_key = models.CharField(max_length=255, blank=True, null=True)
    pinata_secret = models.CharField(max_length=255, blank=True, null=True)
    is_ipfs_connected = models.BooleanField(default=False)

    def unread_notifications_count(self):
        return self.notifications.filter(is_read=False).count()

class Case(models.Model):
    CASE_TYPES = (
        ('public', 'Public'),
        ('private', 'Private'),
    )
    CASE_STATUS = (
        ('active', 'Active'),
        ('closed', 'Closed'),
        ('archived', 'Archived'),
    )
    case_type = models.CharField(max_length=10, choices=CASE_TYPES)
    name = models.CharField(max_length=255)
    case_number = models.CharField(max_length=50, unique=True)
    description = models.TextField()
    status = models.CharField(max_length=10, choices=CASE_STATUS, default='active')
    location = models.CharField(max_length=255)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='created_cases')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    archived_at = models.DateTimeField(null=True, blank=True)
    shared_with = models.ManyToManyField(CustomUser, related_name='shared_cases', blank=True)

class CaseFile(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='files')
    file_name = models.CharField(max_length=255)
    cid = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_type = models.CharField(max_length=10)  # pdf, image, etc.

class DisclosureForm(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='disclosure_forms')
    added_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)
    form_pdf_cid = models.CharField(max_length=255)
    form_name = models.CharField(max_length=255)

class CaseActivityLog(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='activity_logs')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    activity = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

class UserRecentCase(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='recent_cases')
    case = models.ForeignKey(Case, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now_add=True)

class Notification(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    case = models.ForeignKey(Case, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)