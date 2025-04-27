from django.contrib import admin
from .models import KYCVerification




class KYCVerificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'document_number', 'document_type', 'status', 'submitted_at')
    ordering = ('submitted_at',)
    search_fields = ('user__email', 'document_number', 'status', 'document_type')
    list_filter = ('status', 'document_type')

admin.site.register(KYCVerification, KYCVerificationAdmin)
