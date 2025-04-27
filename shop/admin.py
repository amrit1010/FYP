from django.contrib import admin
from .models import *
from core.models import CustomUser

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'vendor', 'status', 'is_flagged', 'created_at')
    list_filter = ('status', 'is_flagged')
    search_fields = ('name', 'description')
    actions = ['approve_products', 'reject_products', 'flag_products', 'unflag_products']

    def approve_products(self, request, queryset):
        queryset.update(status='approved')
    approve_products.short_description = "Approve selected products"

    def reject_products(self, request, queryset):
        queryset.update(status='rejected')
    reject_products.short_description = "Reject selected products"

    def flag_products(self, request, queryset):
        queryset.update(is_flagged=True)
    flag_products.short_description = "Flag selected products"

    def unflag_products(self, request, queryset):
        queryset.update(is_flagged=False)
    unflag_products.short_description = "Unflag selected products"


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display=('name',)
    
@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display=('name',)
    
@admin.register(BidOrder)
class BidOrderAdmin(admin.ModelAdmin):
    list_display=('user','auction','product','bid_amount','ordered_at','payment_status','status',)
    
@admin.register(Reviews)
class ReviewsAdmin(admin.ModelAdmin):
    list_display=('product','review','name','email','comment',)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display=('name',)

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['cart', 'product', 'quantity', 'created_at']
    
@admin.register(Checkout)
class CheckoutAdmin(admin.ModelAdmin):
    list_display=('user','first_name','last_name','email','address','city','postal_code','phone',)
    
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display=('product','price','quantity','total_price','payment_method','status',)
    
@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display=('name','email','subject','message','created_at')

# Auction Admin
@admin.register(Auction)
class AuctionAdmin(admin.ModelAdmin):
    list_display = ('product', 'start_time', 'end_time', 'starting_bid', 'highest_bid', 'highest_bidder', 'is_active', 'time_left')
    search_fields = ('product__name', 'highest_bidder__username')
    list_filter = ('is_active', 'start_time', 'end_time')
    actions = ['approve_auctions', 'reject_auctions']
    list_per_page = 20
    
    fieldsets = (
        (None, {
            'fields': ('product', 'start_time', 'end_time', 'starting_bid', 'highest_bid', 'highest_bidder', 'is_active')
        }),
    )

    def time_left(self, obj):
        return obj.time_left()
    time_left.short_description = 'Time Remaining'

    def get_queryset(self, request):
        # Optimize queries
        return super().get_queryset(request).select_related('product', 'highest_bidder')
    
    def approve_auctions(self, request, queryset):
        queryset.update(status='approved')
    approve_auctions.short_description = "Approve selected auctions"

    def reject_auctions(self, request, queryset):
        queryset.update(status='rejected')
    reject_auctions.short_description = "Reject selected auctions"

# Bid Admin
@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = ('auction', 'bidder', 'amount', 'created_at')
    search_fields = ('auction__product__name', 'bidder__username')
    list_filter = ('created_at',)
    list_per_page = 20
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('auction__product', 'bidder')
    


admin.site.register(RefundRequest)
