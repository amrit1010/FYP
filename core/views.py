from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.urls import reverse
from django.contrib.auth import logout
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from user.forms import KYCForm
from django.urls import reverse
from .models import *
from user.models import *
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str


# Create your views here.

User = get_user_model()


def register(request):
    if request.method == 'POST':
        try:
            full_name = request.POST.get('full_name', '').strip()
            email = request.POST.get('email', '').strip()
            phone = request.POST.get('phone', '').strip()
            password = request.POST.get('password', '')
            role = request.POST.get('role', 'user')

            print("-------------------")
            # Check if any required field is empty
            if not full_name or not email or not phone or not password:
                messages.error(request, "All fields are required.")
                return redirect('core:register')

            # Check if email or phone already exists
            # if User.objects.filter(email=email).exists():
            #     messages.error(request, "Email is already registered.")
            #     return redirect('register')

            if User.objects.filter(phone=phone).exists():
                messages.error(request, "Phone number is already registered.")
                return redirect('core:register')

            # Create user but keep inactive until email confirmation
            user = User.objects.create_user(email=email, full_name=full_name, phone=phone, password=password)
            user.role = role
            user.is_active = False
            user.save()

            # Generate Email Verification Link
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            activation_link = request.build_absolute_uri(reverse('core:activate', args=[uid, token]))

            # Email Content
            email_subject = 'Activate Your Account'
            email_body = f'Hi {full_name},\n\nClick the link to activate your account: {activation_link}\n\nThank you!'

            try:
                send_mail(
                    email_subject,
                    email_body,
                    settings.EMAIL_HOST_USER,
                    [email],
                    fail_silently=False,  # Change to True if you want to suppress email errors
                )
                messages.success(request, "Registration successful! Check your email to confirm your account.")
            except Exception as e:
                messages.error(request, f"Error sending email: {e}")
                return redirect('core:register')

            return redirect('core:check_email')  # Redirect to a 'Check Email' page

        except Exception as e:
            messages.error(request, f"An error occurred: {e}")
            return redirect('core:register')

    return render(request, 'core/signup.html')



def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, "Your account has been activated. You can now login.")
        return redirect('core:login')
    else:
        messages.error(request, "Invalid activation link.")
        return redirect('core:register')
    



def user_login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        remember = request.POST.get('remember')
        ip_address = request.META.get('REMOTE_ADDR')  # Get user's IP address
        user_agent = request.META.get('HTTP_USER_AGENT', '')  # Get user agent (browser info)

        print('------------------------------')
        print("Attempting Login for:", email)
        
        # Attempt authentication
        user = authenticate(request, email=email, password=password)

        # Log the attempt (successful or failed)
        if user:
            print("Authenticated User:", email)  # Debugging

            # Log successful login attempt
            SecurityLog.objects.create(
                user=user,
                event_type="LOGIN",
                ip_address=ip_address,
                user_agent=user_agent
            )

            login(request, user)
            request.session.set_expiry(0 if not remember else 604800)  # 7 days
            
            kyc_exists = KYCVerification.objects.filter(user=user).exists()
            print(f"KYC Exists for {user.email}: {kyc_exists}")  # Debugging

            # Check if the logged-in user is a vendor and has not completed KYC
            if user.role != 'superadmin' and not kyc_exists:
                print(f"Redirecting {user.email} to KYC Page.")  # Debugging
                messages.info(request, "Please complete KYC verification before proceeding.")
                return redirect('customer:kyc_verification')

            # Redirect based on user role
            if user.role == 'vendor':
                return redirect('dashboard:vendor_dashboard')  # Redirect to vendor dashboard
            elif user.role == 'superadmin':
                return redirect('admin:index')  # Redirect to superadmin dashboard
            elif user.role == 'user':
                return redirect('shop:home')  # Redirect regular users to the home page
            else:
                # Handle any other roles (if they exist)
                messages.error(request, "Unknown user role. Please contact support.")
                return redirect('core:login')

        else:
            # Log failed login attempt
            print(f"Invalid credentials for {email}")  # Debugging
            SecurityLog.objects.create(
                event_type="FAILED_LOGIN",
                ip_address=ip_address,
                user_agent=user_agent,
                additional_info=f"Failed login attempt for email: {email}"
            )
            messages.error(request, "Invalid email or password.")
            return redirect('core:login')  # Redirect back to login page if authentication fails

    return render(request, 'core/signin.html')



def check_email(request):
    return render(request, 'core/check_email.html')


def user_logout(request):
    logout(request)
    return redirect('shop:home')  # Redirect to login page after logout


@login_required
def dashboard_redirect(request):
    if request.user.role == 'superadmin':
        return redirect('supadmin:superadmin_dashboard')
    elif request.user.role == 'vendor':
        return redirect('vendor:vendor_dashboard')  
    else:
        return redirect('customer:customer_dashboard')
    


# Forgot Password View
def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = CustomUser.objects.get(email=email)
            # Generate token and UID
            token_generator = PasswordResetTokenGenerator()
            token = token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            # Create reset link
            reset_link = request.build_absolute_uri(
                reverse('core:reset_password', kwargs={'uidb64': uid, 'token': token})
            )
            # Send email
            subject = "Password Reset Request"
            message = f"Hi {user.full_name},\n\nClick the link below to reset your password:\n{reset_link}\n\nIf you didn’t request this, please ignore this email."
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            messages.success(request, "A password reset link has been sent to your email.")
            return redirect('core:check_mail')
        except CustomUser.DoesNotExist:
            messages.error(request, "No account found with this email address.")
            return render(request, 'core/forgot_password.html')
    return render(request, 'core/forgot_password.html')

# Reset Password View
def reset_password(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None

    token_generator = PasswordResetTokenGenerator()
    if user and token_generator.check_token(user, token):
        if request.method == 'POST':
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')
            if password == confirm_password:
                user.set_password(password)
                user.save()
                ip = request.META.get('REMOTE_ADDR')
                SecurityLog.objects.create(
                    user=user,
                    event_type='PASSWORD_RESET',
                    ip_address=ip
                )
                messages.success(request, "Your password has been reset successfully. Please log in.")
                return redirect('core:login')
            else:
                messages.error(request, "Passwords do not match.")
                return render(request, 'core/reset_password.html', {'uidb64': uidb64, 'token': token})
        return render(request, 'core/reset_password.html', {'uidb64': uidb64, 'token': token})
    else:
        messages.error(request, "The reset link is invalid or has expired.")
        return redirect('core:login')
    


def check_mail(request):
    return render(request, 'core/check_email.html')