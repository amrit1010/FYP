from django.shortcuts import render

def check_blacklisted(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_blacklisted:
            return render(request, 'shop/403.html', status=403)
        return view_func(request, *args, **kwargs)
    return wrapper