from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import ProfileEditForm,CustomPasswordChangeForm
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from shop.models import Product
from .forms import ProductForm
from django.urls import reverse
from shop.custom_decorator import check_blacklisted
from datetime import timedelta
from django.utils import timezone
from django.db.models.functions import TruncDate
from django.db.models import Count, Sum, F, ExpressionWrapper, fields
import json

# Create your views here.
@check_blacklisted
@login_required
def vendor_dashboard(request):
    # Ensure the user is a vendor
    if not request.user.is_authenticated or request.user.role != 'vendor':
        return render(request, 'dashboard/access_denied.html')

    # Get the vendor's products
    vendor_products = Product.objects.filter(vendor=request.user)

    # Total Products
    total_products = vendor_products.count()

    # Auction Products
    auction_products = vendor_products.filter(product_type='auction').count()

    # Total Revenue
    total_revenue = (
        Order.objects
        .filter(product__in=vendor_products)
        .aggregate(total_revenue=Sum('total_price'))
        .get('total_revenue', 0) or 0
    )

    # Total Sales
    total_sales = Order.objects.filter(product__in=vendor_products).count()

    # Sales Trends: Total sales per day for the last 7 days
    sales_trends = (
        Order.objects
        .filter(product__in=vendor_products, created_at__gte=timezone.now() - timedelta(days=7))
        .annotate(date=TruncDate('created_at'))
        .values('date')
        .annotate(total_sales=Sum('total_price'))
        .order_by('date')
    )

    # Convert sales_trends to a JSON-serializable format
    sales_trends_data = [
        {
            'date': trend['date'].strftime("%Y-%m-%d"),  # Convert date to string
            'total_sales': float(trend['total_sales'])   # Ensure Decimal is converted to float
        }
        for trend in sales_trends
    ]

    # Auction Performance: Total bids per product
    auction_performance = (
        Auction.objects
        .filter(product__in=vendor_products)
        .annotate(total_bids=Count('bids'))
        .values('product__name', 'total_bids')
    )

    # Convert auction_performance to a JSON-serializable format
    auction_performance_data = list(auction_performance)

    # Active Buyers: Users who placed the most orders
    active_buyers = (
        Order.objects
        .filter(product__in=vendor_products)
        .values('user__email')
        .annotate(total_orders=Count('id'))
        .order_by('-total_orders')[:10]  # Top 10 active buyers
    )

    # Convert active_buyers to a JSON-serializable format
    active_buyers_data = list(active_buyers)

    context = {
        "total_products": total_products,
        "auction_products": auction_products,
        "total_revenue": total_revenue,
        "total_sales": total_sales,
        "sales_trends": json.dumps(sales_trends_data),  # Use the serializable data
        "auction_performance": json.dumps(auction_performance_data),  # Use the serializable data
        "active_buyers": json.dumps(active_buyers_data),  # Use the serializable data
    }
    return render(request, 'dashboard/home.html', context)


@login_required
@check_blacklisted
def profile(request):
    user = request.user
    return render(request, 'dashboard/profile.html', {'user': user})

@check_blacklisted
@login_required
def profile_edit(request):
    user = request.user
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('dashboard:vendor-profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProfileEditForm(instance=user)
    return render(request, 'dashboard/profile_edit.html', {'form': form})

from django.contrib.auth import logout
@login_required
def change_password(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            logout(request)  # Log out the user
            messages.success(request, 'Your password was successfully updated! Please log in again.')
            return redirect('core:login')  # Redirect to core:login
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomPasswordChangeForm(user=request.user)
    return render(request, 'dashboard/change_password.html', {'form': form})

@check_blacklisted
@login_required
def vendor_products(request):
    # Check if user is a vendor and KYC verified
    if request.user.role != 'vendor' or not request.user.kyc_verified:
        return render(request, 'dashboard/access_denied.html', {
            'message': 'Only KYC-verified vendors can access this section.'
        })

    product_type = request.GET.get('type', 'selling')
    if product_type not in ['selling', 'auction', 'renting']:
        product_type = 'selling'

    products = Product.objects.filter(
        vendor=request.user,
        product_type=product_type
    ).select_related('categories', 'brand', 'size').prefetch_related('auction').order_by('-created_at')

    context = {
        'vendor': request.user,
        'product_type': product_type,
        'products': products,
    }
    return render(request, 'dashboard/vendor_products.html', context)

from .forms import AuctionProductForm
from shop.models import Auction
@check_blacklisted
@login_required
def add_product(request):
    # Check if user is a vendor and KYC verified
    if request.user.role != 'vendor' or not request.user.kyc_verified:
        return render(request, 'dashboard/access_denied.html', {
            'message': 'Only KYC-verified vendors can add products.'
        })

    product_type = request.GET.get('type', 'selling')
    print(f"Add Product - product_type: {product_type}")  # Debug
    if product_type not in ['selling', 'auction', 'renting']:
        product_type = 'selling'

    if request.method == 'POST':
        form = AuctionProductForm(request.POST, request.FILES) if product_type == 'auction' else ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.vendor = request.user
            product.product_type = product_type
            product.save()
            if product_type == 'auction':
                Auction.objects.create(
                    product=product,
                    start_time=form.cleaned_data['start_time'],
                    end_time=form.cleaned_data['end_time'],
                    starting_bid=form.cleaned_data['starting_bid']
                )
            return redirect(f"{reverse('dashboard:vendor_products')}?type={product_type}")
        else:
            print(form.errors)
    else:
        form = AuctionProductForm(initial={'product_type': product_type}) if product_type == 'auction' else ProductForm(initial={'product_type': product_type})

    context = {
        'form': form,
        'vendor': request.user,
        'product_type': product_type,
    }
    return render(request, 'dashboard/add_product.html', context)


@check_blacklisted
@login_required
def edit_product(request, product_id):
    # Check if user is a vendor and KYC verified
    if request.user.role != 'vendor' or not request.user.kyc_verified:
        return render(request, 'dashboard/access_denied.html', {
            'message': 'Only KYC-verified vendors can edit products.'
        })
@check_blacklisted
@login_required
def edit_product(request, product_id):
    # Check if user is a vendor and KYC verified
    if request.user.role != 'vendor' or not request.user.kyc_verified:
        return render(request, 'dashboard/access_denied.html', {
            'message': 'Only KYC-verified vendors can edit products.'
        })

    # Get the product and ensure it belongs to the vendor
    product = get_object_or_404(Product, id=product_id, vendor=request.user)
    product_type = product.product_type  # Use the product's actual type, not GET parameter
    auction = product.auction if product_type == 'auction' else None

    if request.method == 'POST':
        # Use AuctionProductForm for auction products, ProductForm otherwise
        form = AuctionProductForm(request.POST, request.FILES, instance=product) if product_type == 'auction' else ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            product = form.save()
            # Handle auction-specific fields
            if product_type == 'auction':
                if auction:
                    # Update existing auction
                    auction.start_time = form.cleaned_data['start_time']
                    auction.end_time = form.cleaned_data['end_time']
                    auction.starting_bid = form.cleaned_data['starting_bid']
                    auction.save()
                else:
                    # Create new auction if it doesn't exist
                    Auction.objects.create(
                        product=product,
                        start_time=form.cleaned_data['start_time'],
                        end_time=form.cleaned_data['end_time'],
                        starting_bid=form.cleaned_data['starting_bid']
                    )
            return redirect(f"{reverse('dashboard:vendor_products')}?type={product_type}")
        else:
            print(form.errors)  # Debug form errors
    else:
        # Initialize form with existing data
        if product_type == 'auction' and auction:
            initial_data = {
                'start_time': auction.start_time,
                'end_time': auction.end_time,
                'starting_bid': auction.starting_bid
            }
            form = AuctionProductForm(instance=product, initial=initial_data)
        else:
            form = ProductForm(instance=product)

    context = {
        'form': form,
        'vendor': request.user,
        'product': product,
        'product_type': product_type,
    }
    return render(request, 'dashboard/edit_product.html', context)


@login_required
def remove_product(request, product_id):
    # Check if user is a vendor and KYC verified
    if request.user.role != 'vendor' or not request.user.kyc_verified:
        return render(request, 'dashboard/access_denied.html', {
            'message': 'Only KYC-verified vendors can remove products.'
        })

    product = get_object_or_404(Product, id=product_id, vendor=request.user)
    product_type = request.GET.get('type', 'selling')
    if product_type not in ['selling', 'auction', 'renting']:
        product_type = 'selling'

    if request.method == 'POST':
        product.delete()
        return redirect(f"{reverse('dashboard:vendor_products')}?type={product_type}")
    return redirect(f"{reverse('dashboard:vendor_products')}?type={product_type}")

from shop.models import ChatMessage
@login_required
@check_blacklisted
def vendor_messages(request):
    # Check if user is a vendor and KYC verified
    if request.user.role != 'vendor' or not request.user.kyc_verified:
        return render(request, 'dashboard/access_denied.html', {
            'message': 'Only KYC-verified vendors can remove products.'
        })
    
    # Get the latest message for each sender-product combination
    messages = ChatMessage.objects.filter(receiver=request.user).order_by('product', '-created_at')
    
    # To avoid duplicates, we can select only the latest message for each product
    latest_messages = []
    seen_products = set()

    for message in messages:
        if message.product not in seen_products:
            latest_messages.append(message)
            seen_products.add(message.product)

    return render(request, 'dashboard/vendor_messages.html', {
        'messages': latest_messages,
    })

from django.db.models import Q
@login_required
@check_blacklisted
def reply_message(request, message_id):
    if request.user.role != 'vendor':
        return render(request, 'dashboard/access_denied.html')
    
    original_message = get_object_or_404(ChatMessage, id=message_id, receiver=request.user)
    conversation = ChatMessage.objects.filter(
        product=original_message.product
    ).filter(
        Q(sender=request.user, receiver=original_message.sender) | 
        Q(sender=original_message.sender, receiver=request.user)
    ).order_by('created_at')
    
    return render(request, 'dashboard/reply_message.html', {
        'original_message': original_message,
        'conversation': conversation,
    })


from shop.models import Order
from django.http import HttpResponse
import logging
from django.core.paginator import Paginator
from django.core.mail import send_mail


logger = logging.getLogger(__name__)
@check_blacklisted
@login_required
def vendor_orders(request):
    """
    Display orders for products uploaded by the logged-in vendor.
    """
    if not hasattr(request.user, 'role') or request.user.role != 'vendor':
        logger.error(f"Non-vendor {request.user} attempted to access vendor orders")
        return HttpResponse("Unauthorized", status=403)

    try:
        # Check if user has role attribute
        logger.info(f"User: {request.user}, Role: {getattr(request.user, 'role', 'None')}")

        # Get vendor products
        vendor_products = Product.objects.filter(vendor=request.user)
        logger.info(f"Found {vendor_products.count()} products for vendor {request.user}")

        # Get orders
        orders = Order.objects.filter(
            product__in=vendor_products
        ).select_related(
            'user', 'product'
        ).order_by('-created_at')
        logger.info(f"Found {orders.count()} orders")

        # Apply status filter
        status_filter = request.GET.get('status', '')
        if status_filter:
            orders = orders.filter(status=status_filter)
            logger.info(f"Filtered to {orders.count()} orders with status {status_filter}")

        # Pagination
        paginator = Paginator(orders, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context = {
            'page_obj': page_obj,
            'status_choices': Order.STATUS_CHOICES,
            'current_status': status_filter,
        }
        
        logger.info(f"Vendor {request.user} viewed their orders")
        return render(request, 'dashboard/vendor_orders.html', context)

    except Product.DoesNotExist:
        logger.error(f"No products found for vendor {request.user}")
        return render(request, 'dashboard/vendor_orders.html', {'error': 'No products found'})
    except Order.DoesNotExist:
        logger.error(f"No orders found for vendor {request.user}")
        return render(request, 'dashboard/vendor_orders.html', {'error': 'No orders found'})
    except Exception as e:
        logger.error(f"Error loading vendor orders for {request.user}: {str(e)}", exc_info=True)
        return render(request, 'dashboard/vendor_orders.html', {
            'error': f'Unable to load orders at this time: {str(e)}'
        })

from django.conf import settings
@login_required
def vendor_order_update(request, order_id):
    """
    Update order status and notify customer via email
    """
    if not hasattr(request.user, 'role') or request.user.role != 'vendor':
        logger.error(f"Non-vendor {request.user} attempted to access order update")
        return HttpResponse("Unauthorized", status=403)

    try:
        order = Order.objects.get(
            id=order_id,
            product__vendor=request.user
        )
        
        if request.method == "POST":
            new_status = request.POST.get('status')
            if new_status in dict(Order.STATUS_CHOICES):
                old_status = order.status
                order.status = new_status
                order.save()

                # Send email notification to customer
                subject = f"Order #{order.id} Status Update"
                message = f"""
                Dear {order.user.full_name},

                Your order id #{order.id} for {order.product.name} has been updated.
                
                Previous Status: {dict(Order.STATUS_CHOICES)[old_status]}
                New Status: {dict(Order.STATUS_CHOICES)[new_status]}
                
                Thank you for shopping with us!
                """
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [order.user.email],
                    fail_silently=False,
                )
                
                logger.info(f"Vendor {request.user} updated order {order.id} status to {new_status}")
                return redirect('dashboard:vendor_orders')
        
        context = {
            'order': order,
            'status_choices': Order.STATUS_CHOICES,
        }
        return render(request, 'dashboard/vendor_order_update.html', context)

    except Order.DoesNotExist:
        logger.error(f"Order {order_id} not found or not owned by vendor {request.user}")
        return HttpResponse("Order not found", status=404)
    except Exception as e:
        logger.error(f"Error updating order {order_id} for {request.user}: {str(e)}")
        return render(request, 'dashboard/vendor_order_update.html', {
            'error': 'Unable to update order at this time'
        })
        
def message(request):
    return render(request, 'dashboard/message.html')
