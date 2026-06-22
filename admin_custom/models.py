from django.db import models
from django.contrib.auth.models import User
from core.models import UserProfile

class Staff(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_profile')
    employee_id = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=100)
    position = models.CharField(max_length=100)
    hire_date = models.DateField()
    phone_number = models.CharField(max_length=15, blank=True)
    emergency_contact = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.position}"

    class Meta:
        ordering = ['user__first_name', 'user__last_name']

# Role model removed - Django's built-in auth system (User, Group, Permission) is sufficient
# No data was stored in this table and it duplicated Django's functionality

# AdminSettings model removed - No configuration data was stored and feature was unused