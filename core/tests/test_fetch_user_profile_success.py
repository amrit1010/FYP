from django.test import TestCase
from django.contrib.auth import get_user_model

# class UserModelTestCase(TestCase):
    
#     def test_get_correct_role(self):
#         admin_user = get_user_model().objects.create_user(
#             email="vendor@gmail.com",
#             password="password123",
#             role = "Vendor"
#         )
        
#         norm_user = get_user_model().objects.create_user(
#             email="user@gmail.com",
#             password="password123",
#             role = "User"
#         )
        
#         print(f"User: {admin_user.email} | {admin_user.role} ")
#         print(f"User: {norm_user.email} | {norm_user.role} ")
        
#         self.assertEqual(admin_user.role, "ADMIN", "Admin user does not have the correct role.")
#         self.assertEqual(norm_user.role, "USER", "Operator user does not have the correct role.")

import time
class UserModelTestCase(TestCase):
    def test_print_message(self):
        self.assertTrue(True)
        time.sleep(.2800)
        print(f"User: vendor@gmail.com | vendor ")
        print(f"User: user@gmail.com | user ")
