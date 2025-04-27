# shop/tasks.py
from celery import shared_task
from django.utils import timezone
from .models import Auction

@shared_task
def finalize_ended_auctions():
    now = timezone.now()
    ended_auctions = Auction.objects.filter(is_active=True, end_time__lte=now)
    for auction in ended_auctions:
        auction.is_active = False
        auction.save()  # This triggers notify_winner()