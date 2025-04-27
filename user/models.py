from django.db import models
from django.conf import settings


class KYCVerification(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    DOCUMENT_TYPE_CHOICES = (
        ('passport', 'Passport'),
        ('id_card', 'ID Card'),
        ('driving_license', 'Driving License'),
        ('other', 'Other'),
    )

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPE_CHOICES, default='other')
    document_number = models.CharField(max_length=100)  # Example field (e.g., Passport/ID)
    document_image = models.ImageField(upload_to='kyc_documents/', blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    submitted_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # Save KYC instance first
        # If approved, update user's kyc_verified field
        if self.status == 'approved':
            self.user.kyc_verified = True
        else:
            self.user.kyc_verified = False
        self.user.save()


    def __str__(self):
        return f"{self.user.email} - {self.status}"





