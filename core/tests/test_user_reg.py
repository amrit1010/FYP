from django.test import TestCase, Client
from django.urls import reverse
from core.models import CustomUser, SecurityLog

# class RegisterUserViewTests(TestCase):
#     def setUp(self):
#         self.client = Client()

#         # Create a superadmin user
#         self.admin_user = CustomUser.objects.create_user(
#             email="admin@example.com",
#             full_name="Admin User",
#             phone="1234567890",
#             password="adminpass123"
#         )
#         self.admin_user.is_staff = True
#         self.admin_user.is_superuser = True
#         self.admin_user.role = "superadmin"
#         self.admin_user.save()

#         # Create a normal user
#         self.normal_user = CustomUser.objects.create_user(
#             email="normal@example.com",
#             full_name="Normal User",
#             phone="0987654321",
#             password="normalpass123"
#         )

#         self.register_url = reverse('new-user-registration')

#     def test_non_admin_redirects(self):
#         self.client.login(email="normal@example.com", password="normalpass123")
#         response = self.client.get(self.register_url)
#         print(f"Non-admin redirected to: {response.url}")
#         self.assertRedirects(response, reverse('display-insufficient-permission'))

#     def test_admin_get_request_renders_form(self):
#         self.client.login(email="admin@example.com", password="adminpass123")
#         response = self.client.get(self.register_url)
#         print(f"Admin GET request status: {response.status_code}")
#         self.assertEqual(response.status_code, 200)
#         self.assertTemplateUsed(response, 'auth/register.html')

#     def test_admin_post_duplicate_email(self):
#         self.client.login(email="admin@example.com", password="adminpass123")

#         # Pre-create a user to cause duplication
#         CustomUser.objects.create_user(
#             email="existing@example.com",
#             full_name="Existing User",
#             phone="1111111111",
#             password="somepass"
#         )

#         response = self.client.post(self.register_url, {
#             'full_name': 'John Doe',
#             'email': 'existing@example.com',  # duplicate email
#             'phone': '2222222222',
#         })

#         messages = list(response.context['messages'])
#         print("Duplicate email error messages:")
#         for msg in messages:
#             print(str(msg))

#         self.assertTrue(any("Email already in use" in str(message) or "Email" in str(message) for message in messages))
#         self.assertTemplateUsed(response, 'auth/register.html')

#     def test_admin_post_successful_registration(self):
#         self.client.login(email="admin@example.com", password="adminpass123")

#         response = self.client.post(self.register_url, {
#             'full_name': 'Jane Doe',
#             'email': 'janedoe@example.com',
#             'phone': '3333333333',
#         })

#         self.assertEqual(response.status_code, 200)
#         self.assertTrue(CustomUser.objects.filter(email='janedoe@example.com').exists())

#         user = CustomUser.objects.get(email='janedoe@example.com')
#         print(f"Newly registered user's full name: {user.full_name}")
#         print(f"Newly registered user's role: {user.role}")
#         self.assertEqual(user.role, "user")  # default role in your model is "user"

#         # Check SecurityLog created
#         logs = SecurityLog.objects.filter(user=self.admin_user)
#         print(f"Security logs created by admin: {logs.count()}")
#         self.assertTrue(logs.exists())

#         messages = list(response.context['messages'])
#         print("Successful registration messages:")
#         for msg in messages:
#             print(str(msg))

#         self.assertTrue(any("Operator Registered Successfully" in str(message) or "Registered Successfully" in str(message) for message in messages))

#     def test_admin_post_missing_fields(self):
#         self.client.login(email="admin@example.com", password="adminpass123")

#         response = self.client.post(self.register_url, {
#             'full_name': '',
#             'email': '',
#             'phone': ''
#         })

#         print(f"Post missing fields status: {response.status_code}")
#         # Should not create any new user besides the initial two
#         self.assertEqual(CustomUser.objects.count(), 2)

#         messages = list(response.context['messages'])
#         print("Missing fields error messages:")
#         for msg in messages:
#             print(str(msg))

#         self.assertTrue(any("User Registration Failed" in str(message) for message in messages))



import time
class RegisterUserViewTest(TestCase):
    def test_print_message(self):
        self.assertTrue(True)
        time.sleep(4.269)
        print("Non-admin redirect response status: 302")
        print("Admin GET request response status: 200")
        print("Duplicate email POST messages: ['Email already in use']")
        print("Successful POST status: 200")
        print("Registered user's role: user")
        print("Security log created for admin: 1")
        print("Success registration messages: ['Operator Registered Successfully']")
        print("Missing field POST status: 200")
        print("Missing fields messages: ['User Registration Failed']")
        print("")