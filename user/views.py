from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import KYCForm,UserProfileForm
from .models import KYCVerification
from django.contrib.auth.decorators import login_required

@login_required(login_url='login')
def index(request):
    return render(request, 'user/index.html')


@login_required
def kyc_verification(request):
    # Check if the user has already submitted the KYC form
    kyc_exists = KYCVerification.objects.filter(user=request.user).exists()

    if kyc_exists:
        return redirect('dashboard:vendor_dashboard') # Redirect to the homepage if KYC already submitted

    if request.method == 'POST':
        form = KYCForm(request.POST, request.FILES)
        if form.is_valid():
            kyc = form.save(commit=False)
            kyc.user = request.user
            kyc.status = 'pending'  # Set status to pending
            kyc.save()
            messages.success(request, "KYC submitted successfully. You can now access the platform.")
             # Redirect based on user role after KYC submission
            if request.user.role == 'vendor':
                return redirect('dashboard:vendor_dashboard')
            elif request.user.role == 'superadmin':
                return redirect('admin:index')
            else:
                return redirect('shop:home')
    else:
        form = KYCForm()

    return render(request, 'user/kyc_verification.html', {'form': form})




@login_required
def profile(request):
    user = request.user
    return render(request, 'user/profile.html', {
        'user': user,
    })


@login_required
def edit_profile(request):
    user = request.user

    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('customer:profile')  # Redirect to the profile page after saving
    else:
        form = UserProfileForm(instance=user)

    return render(request, 'user/edit_profile.html', {
        'form': form,
    })






    
