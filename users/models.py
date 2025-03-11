from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # Add additional fields here
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return self.user.username

class Record(models.Model):
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    address = models.TextField()
    department = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Techsupport(models.Model):
    SUPPORT_CHOICES = [
        ('internet', 'Internet Issues'),
        ('cable', 'Cable Issues'),
        ('phone', 'Phone Issues'),
        ('device_setup', 'Device Setup'),
        ('replacement', 'Replacement Device Request'),
        ('software_install', 'Software Installation'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    support_type = models.CharField(max_length=50, choices=SUPPORT_CHOICES)
    description = models.TextField()
    status = models.CharField(max_length=20, default='open')  # e.g., open, in_progress, resolved
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.support_type}"
    
class AccountInfo(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    account_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    invoices = models.TextField(blank=True)  # Could be a JSON field or a related model for detailed invoices
    plan_details = models.CharField(max_length=100)  # e.g., plan name or description
    contact_details = models.TextField(blank=True)  # To store updated contact information
    payment_status = models.CharField(max_length=20, default='pending')  # e.g., pending, completed

    def __str__(self):
        return f"{self.user.username} - Account Info"