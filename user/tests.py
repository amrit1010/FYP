from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import KYCVerification
from .forms import KYCForm
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()

class KYCVerificationViewTest(TestCase):
    def setUp(self):
        self.client = Client()

        self.vendor_user = User.objects.create_user(
            email='vendor@example.com',
            password='testpassword'
        )
        self.vendor_user.role = 'vendor'
        self.vendor_user.save()

        self.superadmin_user = User.objects.create_user(
            email='admin@example.com',
            password='testpassword'
        )
        self.superadmin_user.role = 'superadmin'
        self.superadmin_user.save()

        self.kyc_url = reverse('user:kyc_verification')  # Make sure your url name is correct

    def test_redirect_if_kyc_already_exists(self):
        # Create existing KYC record
        KYCVerification.objects.create(user=self.vendor_user, document_type='passport', document_number='12345678')

        self.client.login(email='vendor@example.com', password='testpassword')
        response = self.client.get(self.kyc_url)
        self.assertRedirects(response, reverse('dashboard:vendor_dashboard'))

    def test_get_request_returns_kyc_form(self):
        self.client.login(email='vendor@example.com', password='testpassword')
        response = self.client.get(self.kyc_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user/kyc_verification.html')
        self.assertIsInstance(response.context['form'], KYCForm)

    def test_successful_kyc_submission_for_vendor(self):
        self.client.login(email='vendor@example.com', password='testpassword')

        # Mock document upload
        mock_file = SimpleUploadedFile("doc.jpg", b"file_content", content_type="image/jpeg")

        data = {
            'document_type': 'passport',
            'document_number': '12345678',
            'document_image': mock_file,
        }
        response = self.client.post(self.kyc_url, data, follow=True)

        self.assertEqual(KYCVerification.objects.filter(user=self.vendor_user).count(), 1)
        kyc_obj = KYCVerification.objects.get(user=self.vendor_user)
        self.assertEqual(kyc_obj.status, 'pending')
        self.assertRedirects(response, reverse('dashboard:vendor_dashboard'))

    def test_successful_kyc_submission_for_superadmin(self):
        self.client.login(email='admin@example.com', password='testpassword')

        mock_file = SimpleUploadedFile("doc.jpg", b"file_content", content_type="image/jpeg")
        data = {
            'document_type': 'id_card',
            'document_number': '987654321',
            'document_image': mock_file,
        }
        response = self.client.post(self.kyc_url, data, follow=True)

        self.assertEqual(KYCVerification.objects.filter(user=self.superadmin_user).count(), 1)
        self.assertRedirects(response, reverse('admin:index'))

    def test_invalid_form_submission(self):
        self.client.login(email='vendor@example.com', password='testpassword')

        # Submit empty form
        data = {}
        response = self.client.post(self.kyc_url, data)

        self.assertEqual(response.status_code, 200)  # Form reloads with errors
        self.assertFormError(response, 'form', 'document_type', 'This field is required.')
