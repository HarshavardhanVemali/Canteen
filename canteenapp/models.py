from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import uuid
from django.utils.timezone import timedelta

class FailedLoginAttempts(models.Model):
    device_id = models.CharField(max_length=255, unique=True)
    attempts = models.PositiveBigIntegerField(default=0)
    is_active = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    
    def __str__(self):
        return f'{self.device_id} - Attempts: {self.attempts}'

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    is_active = models.BooleanField(default=True)

    ROLE_CHOICES = [
        ('user', 'User'),
        ('delivery_person', 'Delivery Person'),
        ('admin', 'Admin'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    address = models.CharField(max_length=255, blank=True, null=True)
    preferences = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.email 

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

class DeliveryPerson(CustomUser):
    vehicle_info = models.CharField(max_length=255, blank=True, null=True)
    delivery_radius = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        verbose_name = 'Delivery Person'
        verbose_name_plural = 'Delivery Persons'

class RegularUser(CustomUser):
    class Meta:
        verbose_name = 'Regular User'
        verbose_name_plural = 'Regular Users'

class Admin(CustomUser):
    department = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        verbose_name = 'Admin'
        verbose_name_plural = 'Admins'

class EmailVerification(models.Model):
    email = models.EmailField()
    verification_code = models.CharField(max_length=64, unique=True)  
    created_at = models.DateTimeField(auto_now_add=True)  
    expires_at = models.DateTimeField() 
    request_id = models.CharField(max_length=128, unique=True) 
    is_verified = models.BooleanField(default=False) 

    def save(self, *args, **kwargs):
        if not self.verification_code:
            self.verification_code = uuid.uuid4().hex
        
        if not self.request_id:
            self.request_id = uuid.uuid4().hex
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=10)
        if self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=10)
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"Verification for {self.email} - {'Verified' if self.is_verified else 'Pending'}"