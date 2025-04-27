from .models import Category, Notification
from django.utils import timezone
from shop.models import Auction,Cart,CartItem


def category_context(request):
    categories = Category.objects.all().order_by('name')
    return {'categories': categories}

def cart_count(request):
    cart_count = 0
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_count = CartItem.objects.filter(cart=cart).count()
    return {"cart_count": cart_count}


def notification_count(request):
    if request.user.is_authenticated:
        ended_auctions = Auction.objects.filter(
            is_active=True,
            end_time__lte=timezone.now(),
            highest_bidder__isnull=False
        )
        for auction in ended_auctions:
            auction.is_active = False
            auction.notify_winner()
            auction.save()

        # Check ending soon notifications
        active_auctions = Auction.objects.filter(is_active=True, end_time__gt=timezone.now())
        for auction in active_auctions:
            auction.notify_ending_soon()  # This now avoids duplicates

        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    else:
        unread_count = 0
    return {'unread_notification_count': unread_count}