from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *

class CustomUserAdmin(UserAdmin):
    # Define the fields to display in the admin list view
    list_display = ('email', 'full_name', 'phone', 'role', 'is_active', 'is_staff','is_blacklisted')
    list_filter = ('role', 'is_blacklisted')
    ordering = ('email',)
    search_fields = ('email', 'full_name', 'phone')
    actions = ['blacklist_users', 'unblacklist_users']

    def blacklist_users(self, request, queryset):
        queryset.update(is_blacklisted=True)
    blacklist_users.short_description = "Blacklist selected users"

    def unblacklist_users(self, request, queryset):
        queryset.update(is_blacklisted=False)
    unblacklist_users.short_description = "Unblacklist selected users"
    # Override fieldsets to exclude 'username' and include your custom fields
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('full_name', 'phone')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'role', 'groups', 'user_permissions', 'is_blacklisted')}),
    )

    # Override add_fieldsets for the "Add" form in admin
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'phone', 'password1', 'password2', 'role', 'is_active', 'is_staff', 'is_superuser'),
        }),
    )

    # Specify the filter options
    list_filter = ('role', 'is_active', 'is_staff', 'is_superuser')

admin.site.register(CustomUser, CustomUserAdmin)


@admin.register(SecurityLog)
class SecurityLogAdmin(admin.ModelAdmin):
    list_display = ("user", "event_type", "ip_address", "timestamp")
    list_filter = ("event_type", "timestamp")



from shop.models import *
from django.urls import path
from django.shortcuts import render
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from django.db.models.functions import TruncDate
@admin.register(SalesReport)
class SalesReportAdmin(admin.ModelAdmin):
    # Hide the "Add" button since this is a report
    def has_add_permission(self, request):
        return False

    # Hide the "Delete" button
    def has_delete_permission(self, request, obj=None):
        return False

    # Use a custom template
    change_list_template = 'core/salesreport/change_list.html'

    def changelist_view(self, request, extra_context=None):
        # Sales Trends: Total sales per day for the last 7 days
        sales_trends = (
            Order.objects
            .filter(created_at__gte=timezone.now() - timedelta(days=7))
            .annotate(date=TruncDate('created_at'))
            .values('date')
            .annotate(total_sales=Sum('total_price'))
            .order_by('date')
        )

        # Total Revenue
        total_revenue = Order.objects.aggregate(total_revenue=Sum('total_price')).get('total_revenue', 0) or 0

        # Total Sales
        total_sales = Order.objects.count()

        context = {
            'sales_trends': list(sales_trends),  # Convert QuerySet to a list
            'total_revenue': total_revenue,
            'total_sales': total_sales,
            **self.admin_site.each_context(request),
        }
        return super().changelist_view(request, extra_context=context)

@admin.register(UserEngagementReport)
class UserEngagementReportAdmin(admin.ModelAdmin):
    # Hide the "Add" button since this is a report
    def has_add_permission(self, request):
        return False

    # Hide the "Delete" button
    def has_delete_permission(self, request, obj=None):
        return False

    # Use a custom template
    change_list_template = 'core/userengagementreport/change_list.html'

    def changelist_view(self, request, extra_context=None):
        # Active Buyers: Users who placed the most orders
        active_buyers = (
            Order.objects
            .values('user__email')
            .annotate(total_orders=Count('id'))
            .order_by('-total_orders')[:10]  # Top 10 active buyers
        )

        # Active Sellers: Vendors with the most products
        active_sellers = (
            Product.objects
            .values('vendor__email')
            .annotate(total_products=Count('id'))
            .order_by('-total_products')[:10]  # Top 10 active sellers
        )

        context = {
            'active_buyers': list(active_buyers),  # Convert QuerySet to a list
            'active_sellers': list(active_sellers),  # Convert QuerySet to a list
            **self.admin_site.each_context(request),
        }
        return super().changelist_view(request, extra_context=context)
    
from django.db.models import Count, Max, Min, Avg
@admin.register(AuctionPerformance)
class AuctionPerformanceAdmin(admin.ModelAdmin):
    # Hide the "Add" button since this is a report
    def has_add_permission(self, request):
        return False

    # Hide the "Delete" button
    def has_delete_permission(self, request, obj=None):
        return False

    # Use a custom template
    change_list_template = 'core/auctionperformance/change_list.html'

    def changelist_view(self, request, extra_context=None):
        # Fetch auction performance data
        auction_performance = (
            Auction.objects
            .annotate(total_bids=Count('bids'))  # Total bids per auction
            .annotate(max_bid=Max('bids__amount'))  # Highest bid per auction
            .values('id', 'product__name', 'total_bids', 'max_bid', 'status')
        )

        # Debug: Print the fetched data
        print("Auction Performance Data:", list(auction_performance))

        # Total Auctions
        total_auctions = Auction.objects.count()

        # Total Bids
        total_bids = Bid.objects.count()

        context = {
            'auction_performance': list(auction_performance),  # Convert QuerySet to a list
            'total_auctions': total_auctions,
            'total_bids': total_bids,
            **self.admin_site.each_context(request),
        }
        return super().changelist_view(request, extra_context=context)