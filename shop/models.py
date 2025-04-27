from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.apps import apps
import uuid



class Category(models.Model):
    name = models.CharField(max_length=255,null=True, blank=False ,verbose_name="Category Name",db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Category"
        indexes = [models.Index(fields=['name'])]   

    def __str__(self):
        return self.name
    
class Brand(models.Model):
    name=models.CharField(max_length=255,null=True, blank=False,verbose_name="Brand Name",db_index=True)
    image = models.ImageField(upload_to='media/brand_imgs/', blank=True, default=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [models.Index(fields=['name'])]

    
    def __str__(self):
        return self.name
    

class Size(models.Model):
    name = models.CharField(max_length=255,null=True, blank=False,verbose_name="Size Name",db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        indexes = [models.Index(fields=['name'])]


    def __str__(self):
        return self.name

class Product(models.Model):
    SELLING = 'selling'
    RENTING = 'renting'
    AUCTION = 'auction'

    PRODUCT_TYPE_CHOICES = [
        (SELLING, 'Selling'),
        (RENTING, 'Renting'),
        (AUCTION, 'Auction'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    vendor = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        limit_choices_to={'role': 'vendor'},
        related_name='shop_products'
    )
    name = models.CharField(max_length=255,null=False, blank=False,verbose_name="Product Name",db_index=True)
    description = models.CharField(max_length=255,null=True, blank=True,db_index=True)
    additional_information = models.CharField(max_length=255,null=True, blank=True,db_index=True)
    price = models.DecimalField(max_digits=10, decimal_places=2,null=False, blank=False,verbose_name="Product Price",db_index=True)
    discount=models.DecimalField(decimal_places=3, max_digits=10,null=True, blank=True,db_index=True)
    availability = models.BooleanField(default=False)
    sku = models.CharField(max_length=100,null=True, blank=True,db_index=True)
    size=models.ForeignKey(Size, on_delete=models.CASCADE,null=True, blank=True,db_index=True)
    image = models.ImageField(upload_to='products/',null=True, blank=True,db_index=True)
    features = models.BooleanField(default=False, db_index=True)
    categories = models.ForeignKey(Category, on_delete=models.CASCADE,null=True, blank=True,db_index=True)
    stock=models.IntegerField(null=True, blank=True,db_index=True)
    brand = models.ForeignKey('Brand', on_delete=models.CASCADE, null=True, blank=True,db_index=True)

    product_type = models.CharField(
        max_length=10, 
        choices=PRODUCT_TYPE_CHOICES, 
        default=SELLING, 
        db_index=True
    )

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    is_flagged = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Product"
        indexes = [models.Index(fields=['name','description','additional_information','price','availability','sku','size','image','features','categories','stock','brand','product_type'])]


    def __str__(self):
        return self.name
    
    def get_review_count(self):
        return self.reviews_set.count()
    
    def save(self, *args, **kwargs):
        if self.pk:  # Only check on updates, not creation
            old_product = Product.objects.get(pk=self.pk)
            if old_product.price > self.price and self.product_type != self.AUCTION:  # Price dropped (exclude auctions)
                self.notify_price_drop(old_product.price, self.price)
        super().save(*args, **kwargs)

    def notify_price_drop(self, old_price, new_price):
        """Notify subscribers of a price drop."""
        subscribers = self.price_drop_subscribers.all()
        for subscription in subscribers:
            if subscription.last_notified_price is None or subscription.last_notified_price > new_price:
                message = f"Price drop alert! {self.name} dropped from ${old_price} to ${new_price}."
                Notification.objects.create(
                    user=subscription.user,
                    message=message,
                    product=self,
                    notification_type='price_drop'
                )
                subscription.last_notified_price = new_price
                subscription.save()


class PriceDropSubscription(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='price_drop_subscriptions')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='price_drop_subscribers')
    subscribed_at = models.DateTimeField(auto_now_add=True)
    last_notified_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Track last price notified

    class Meta:
        unique_together = ('user', 'product')  # Prevent duplicate subscriptions

    def __str__(self):
        return f"{self.user} subscribed to {self.product}"
    
    
class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('win', 'Auction Win'),
        ('outbid', 'Outbid Alert'),
        ('ending_soon', 'Ending Soon Alert'),
        ('price_drop', 'Price Drop Alert'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    auction = models.ForeignKey('Auction', on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey('Product', on_delete=models.CASCADE, null=True, blank=True)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='win')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.user}: {self.message[:50]}"
    
class Auction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    product = models.OneToOneField(Product, on_delete=models.CASCADE, limit_choices_to={'product_type': 'auction'}, related_name='auction')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    starting_bid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    highest_bid = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    highest_bidder = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='winning_bids')
    is_active = models.BooleanField(default=True)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Auction"
        indexes = [models.Index(fields=['start_time', 'end_time', 'is_active'])]

    def __str__(self):
        return f"Auction for {self.product.name}"

    def time_left(self):
        now = timezone.now()
        if now >= self.end_time:
            return "Auction Ended"
        delta = self.end_time - now
        return f"{delta.days} days, {delta.seconds // 3600} hours, {(delta.seconds // 60) % 60} minutes"

    def update_highest_bid(self, bid_amount, bidder):
        if self.is_active and (self.highest_bid is None or bid_amount > self.highest_bid):
            self.highest_bid = bid_amount
            self.highest_bidder = bidder
            self.save()

    def save(self, *args, **kwargs):
        now = timezone.now()
        was_active = self.is_active
        # Update is_active based on current time and end_time
        self.is_active = self.end_time > now and self.start_time <= now
        super().save(*args, **kwargs)
        # Check if auction has ended and hasn't been notified yet
        # Notify winner only if auction has ended and hasn't been notified
       # Notify winner if auction just ended
        if was_active and not self.is_active and self.highest_bidder:
            self.notify_winner()


    def notify_winner(self):
        if self.highest_bidder and not Notification.objects.filter(
            auction=self, 
            user=self.highest_bidder,
            notification_type='win'
        ).exists():
            if not hasattr(self, 'order'):
                BidOrder.objects.create(
                    user=self.highest_bidder,
                    auction=self,
                    product=self.product,
                    bid_amount=self.highest_bid
                )
            message = f"Congratulations! You won the auction for {self.product.name} with a bid of ${self.highest_bid}!"
            Notification.objects.create(
                user=self.highest_bidder,
                message=message,
                auction=self,
                notification_type='win'
            )

    def notify_outbid(self, previous_bidder, new_bid_amount):
        if previous_bidder and self.is_active and timezone.now() < self.end_time:
            message = f"You’ve been outbid on {self.product.name}! New highest bid is ${new_bid_amount}. Place a higher bid now."
            Notification.objects.create(
                user=previous_bidder,
                message=message,
                auction=self,
                notification_type='outbid'
            )

    def notify_ending_soon(self):
        if self.is_active and timezone.now() < self.end_time:
            time_left = self.end_time - timezone.now()
            if time_left <= timedelta(minutes=15):  # Notify 15 mins before end
                UserModel = apps.get_model(settings.AUTH_USER_MODEL)
                for bidder in self.bids.values('bidder').distinct():
                    user = UserModel.objects.get(id=bidder['bidder'])
                    # Check if an "ending soon" notification already exists for this user and auction
                    if not Notification.objects.filter(
                        user=user,
                        auction=self,
                        notification_type='ending_soon',
                        created_at__gte=timezone.now() - timedelta(minutes=15)  # Only check last 15 mins
                    ).exists():
                        message = f"Auction for {self.product.name} is ending in {int(time_left.total_seconds() // 60)} minutes! Current bid: ${self.highest_bid or self.starting_bid}."
                        Notification.objects.create(
                            user=user,
                            message=message,
                            auction=self,
                            notification_type='ending_soon'
                        )


class Bid(models.Model):
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE, related_name='bids')
    bidder = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bids')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Bid"
        indexes = [models.Index(fields=['auction', 'created_at'])]

    def __str__(self):
        return f"{self.amount} by {self.bidder} on {self.auction}"
    
    def save(self, *args, **kwargs):
        if self.pk is None:  # Only trigger on new bids, not updates
            # Store the previous highest bidder before saving
            previous_highest_bidder = self.auction.highest_bidder
            super().save(*args, **kwargs)
            # Update the auction's highest bid and bidder
            self.auction.update_highest_bid(self.amount, self.bidder)
            # Notify the previous highest bidder if they were outbid
            if previous_highest_bidder and previous_highest_bidder != self.bidder:
                self.auction.notify_outbid(previous_highest_bidder, self.amount)
        else:
            super().save(*args, **kwargs)
        
class BidOrder(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('paid', 'Paid'),
    )
    Payment_Method = {
        ('Cash on Delevery', 'Cash on Delevery'),
        ('Khalti', 'Khalti'),
        
    }
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    auction = models.OneToOneField('Auction', on_delete=models.CASCADE, related_name='order')
    product = models.ForeignKey('Product', on_delete=models.PROTECT)
    bid_amount = models.DecimalField(max_digits=10, decimal_places=2)
    ordered_at = models.DateTimeField(auto_now_add=True)
    payment_status = models.CharField(max_length=255, choices=Payment_Method, default='Khalti')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending') 
    
    def __str__(self):
        return f"Order for {self.product.name} "


class Reviews(models.Model):
    product=models.ForeignKey(Product, on_delete=models.CASCADE,db_index=True)
    review=models.IntegerField(default=0,null=True, blank=False)
    name=models.CharField(max_length=100,db_index=True)
    email=models.EmailField()
    comment=models.TextField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Product Review"
        indexes = [models.Index(fields=['product','name'])]

    
    def __str__(self):
        return self.product.name
    

class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="shop_cart")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart - {self.user.full_name}"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)   
    
    def __str__(self):
        return f"{self.quantity} x {self.product.name}"  # Fixed to use cart.user


class Checkout(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, db_index=True)
    first_name = models.CharField(max_length=100,db_index=True)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(db_index=True)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    phone=models.CharField(max_length=20,db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Checkout"
        indexes = [models.Index(fields=['user','first_name','email','phone'])]


    def __str__(self):
        return f"Order {self.id} by {self.user}"

class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    )
    Payment_Method = {
        ('Cash on Delevery', 'Cash on Delevery'),
        ('Khalti', 'Khalti'),
        
    }
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders', default=1)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    total_price=models.DecimalField(max_digits=10, decimal_places=2)
    payment_method=models.CharField(max_length=255,db_index=True)
    status = models.CharField(max_length=255, choices=STATUS_CHOICES, default='pending', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "All Order"
        indexes = [models.Index(fields=['product','payment_method','status'])]

    def __str__(self):
        return f"{self.quantity} x {self.product}"
    
class Contact(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    subject = models.CharField(max_length=255)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.subject}"
    


# models.py
class ChatMessage(models.Model):
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_messages'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='chat_messages'
    )
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']
        indexes = [models.Index(fields=['product', 'created_at'])]

    def __str__(self):
        return f"Chat about {self.product.name} from {self.sender} to {self.receiver}"
    


class RefundRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='refund_requests')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='refund_requests')
    reason = models.TextField(max_length=500, help_text="Reason for refund request")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    admin_notes = models.TextField(max_length=500, blank=True, null=True, help_text="Notes from admin on approval/rejection")

    class Meta:
        verbose_name = "Refund Request"
        verbose_name_plural = "Refund Requests"
        indexes = [models.Index(fields=['status', 'created_at'])]

    def __str__(self):
        return f"Refund #{self.id} for Order #{self.order.id} - {self.status}"