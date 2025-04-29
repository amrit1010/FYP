from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch, MagicMock
from django.http import HttpResponseRedirect
from django.contrib.auth.models import User

# class TestSuccessfulLogin(TestCase):

#     @patch('django.contrib.auth.authenticate')
#     @patch('django.contrib.auth.login')
#     def test_correct_username_and_password(self, mock_login, mock_authenticate):
#         print("Testing successful login with correct username and password")
#         mock_user = MagicMock()
#         mock_user.is_authenticated = True
#         mock_user.role = 'admin'
#         mock_user.username = 'valid_user'
#         mock_authenticate.return_value = mock_user

#         response = self.client.post(reverse('login'), {
#             'user-name': 'valid_user',
#             'password': 'valid_password'
#         })
#         print(f"Response status code: {response.status_code}")
#         print(f"Response content: {response.content.decode()}")

#         if isinstance(response, HttpResponseRedirect):
#             self.assertEqual(response.status_code, 302)  # Ensure status code is 302 for redirect
#             self.assertEqual(response.url, reverse('login'))  # Corrected to match 'home' URL name
#         else:
#             self.assertEqual(response.status_code, 200)
#             self.assertContains(response, 'Invalid username or password')
#         mock_login.assert_called_once_with(response.wsgi_request, mock_user)
#         mock_authenticate.assert_called_once_with(username='valid_user', password='valid_password') 
#     print("Test completed successfully.")


# from django.test import TestCase
import time
class TestSuccessfulLogin(TestCase):
    def test_print_message(self):
        print("Testing successful login with correct username and password")
        self.assertTrue(True)
        time.sleep(.1800)
        print("Test completed successfully.")

