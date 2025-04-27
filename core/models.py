from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Group, Permission
from django.db import models
from django.utils.timezone import now
from shop.models import Auction


class CustomUserManager(BaseUserManager):
    def create_user(self, email, full_name, phone, password=None):
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, full_name=full_name, phone=phone)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, full_name, phone, password):
        user = self.create_user(email, full_name, phone, password)
        user.is_superuser = True
        user.is_staff = True
        user.role = 'superadmin'
        user.save(using=self._db)
        return user

class CustomUser(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ('superadmin', 'Super Admin'),
        ('vendor', 'Vendor'),
        ('user', 'User'),
    )

    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=15, unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    kyc_verified = models.BooleanField(default=False)
    is_blacklisted = models.BooleanField(default=False)

    groups = models.ManyToManyField(Group, related_name="customuser_groups", blank=True)
    user_permissions = models.ManyToManyField(Permission, related_name="customuser_permissions", blank=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name', 'phone']

    def __str__(self):
        return self.email
    
    
class SecurityLog(models.Model):
    EVENT_CHOICES = [
        ('FAILED_LOGIN', 'Failed Login'),
        ('LOGIN', 'Login'),
        ('PASSWORD_RESET', 'Password Reset'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    event_type = models.CharField(max_length=50, choices=EVENT_CHOICES)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(default=now)
    additional_info = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user} - {self.event_type} at {self.timestamp}"

class SalesReport(CustomUser):  # Inherit from CustomUser
    class Meta:
        proxy = True  # Mark this as a proxy model
        verbose_name = "Sales Report"
        verbose_name_plural = "Sales Reports"
        app_label = "core"  # Group under the 'core' app

    def __str__(self):
        return "Sales Report"

class UserEngagementReport(CustomUser):  # Inherit from CustomUser
    class Meta:
        proxy = True  # Mark this as a proxy model
        verbose_name = "User Engagement Report"
        verbose_name_plural = "User Engagement Reports"
        app_label = "core"  # Group under the 'core' app

    def __str__(self):
        return "User Engagement Report"
    
class AuctionPerformance(Auction):
    class Meta:
        proxy = True  # Mark this as a proxy model
        verbose_name = "Auction Performance"
        verbose_name_plural = "Auction Performance Reports"
        app_label = "core"  # Group under the 'core' app

    def __str__(self):
        return "Auction Performance Report"