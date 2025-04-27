import os
from dotenv import load_dotenv
from django.shortcuts import render,get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import *
from datetime import timedelta
from django.utils import timezone
from django.contrib import messages
from .forms import *
from django.db.models import Q
from django.db.models import Count
from .custom_decorator import check_blacklisted




# Load environment variables
load_dotenv()

# Retrieve the Khalti secret key
KHALTI_SECRET_KEY = os.getenv('KHALTI_SECRET_KEY')

now = timezone.now()

def home(request):
    categories = Category.objects.all().order_by('name')

    # Get products added in the last 30 days
    time_threshold = now - timedelta(days=30)
    new_arrival = Product.objects.filter(created_at__gte=time_threshold, status='approved', product_type = "selling")

    # Get only selling products
    selling_products = Product.objects.filter(product_type='selling', status='approved')
    initial_products = selling_products[:5]
    
    featured_products = Product.objects.filter(features=True,status='approved')[:5]
    brand=Brand.objects.all() 

    products_with_comment_count = Product.objects.annotate(comment_count=Count('reviews'))

    auctions = Auction.objects.filter(
        is_active=True,
        start_time__lte=timezone.now(),
        end_time__gt=timezone.now(),
        product__status='approved'
    ).select_related('product').order_by('end_time')[:2]
    print("---------")
    print(auctions)

# Fetch the latest upcoming auction
    upcoming_auction = Auction.objects.filter(
        start_time__gt=timezone.now(),  # Starts in the future
        status='approved',              # Only approved auctions
        product__status='approved'      # Only approved products
    ).select_related('product').order_by('start_time').first()

    context = {
        'categories': categories,
        'selling_products': selling_products,
        'initial_products': initial_products,
        'new_arrival': new_arrival,
        'featured_products': featured_products,
        'brand': brand,
        'products_with_comment_count': products_with_comment_count,
        'auctions': auctions,
        'upcoming_auction': upcoming_auction,
    }

    return render(request, "home.html", context)

def search_view(request):
    query = request.POST.get('query', '') if request.method == 'POST' else request.GET.get('query', '')
    category_id = request.POST.get('category_id', '') if request.method == 'POST' else request.GET.get('category_id', '')
    
    products = Product.objects.filter(status='approved').select_related('categories')
    
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(additional_information__icontains=query) |
            Q(categories__name__icontains=query)
        )
    
    category = None
    if category_id:
        products = products.filter(categories__id=category_id)
        category = get_object_or_404(Category, id=category_id)
    
    # Group products by category
    products_by_category = {}
    for product in products:
        category_name = product.categories.name if product.categories else "Uncategorized"
        if category_name not in products_by_category:
            products_by_category[category_name] = []
        products_by_category[category_name].append(product)
    
    categories = Category.objects.all()
    
    context = {
        'products_by_category': products_by_category,  # Dictionary of category: products
        'query': query,
        'category_id': category_id,
        'categories': categories,
        'category': category,
    }
    return render(request, 'shop/search.html', context)


def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id, status='approved')
    reviews = Reviews.objects.filter(product=product).order_by('-created_at')

    # Initialize variables
    has_purchased = False
    form = ReviewForm()
    initial_quantity = 1

    # Check if the user is logged in
    if request.user.is_authenticated:
        # Check if the user has purchased the product
        has_purchased = Order.objects.filter(user=request.user, product=product).exists()


# Check if product is in cart and get current quantity
        try:
            cart = Cart.objects.get(user=request.user)
            cart_item = CartItem.objects.filter(cart=cart, product=product).first()
            if cart_item:
                initial_quantity = cart_item.quantity
        except Cart.DoesNotExist:
            pass


        if request.method == 'POST':
            if not has_purchased:
                # If the user hasn't purchased the product, show an error message
                return render(request, 'shop/product-detail.html', {
                    'product': product,
                    'reviews': reviews,
                    'form': form,
                    'error_message': 'You must purchase this product before submitting a review.',
                    'initial_quantity': initial_quantity,
                })

            form = ReviewForm(request.POST)
            if form.is_valid():
                # Save the new review
                review = form.save(commit=False)
                review.product = product  # Associate the review with the product
                review.user = request.user  # Associate the review with the logged-in user
                review.save()
                return redirect('shop:product_detail', product_id=product.id)
        else:
            # Pre-fill the form with the logged-in user's name and email
            initial_data = {
               'name': request.user.full_name,
                'email': request.user.email,
            }
            form = ReviewForm(initial=initial_data)

    return render(request, 'shop/product-detail.html', {
        'product': product,
        'reviews': reviews,
        'form': form,
        'has_purchased': has_purchased,  # Pass this to the template to conditionally display the form
        'user_is_authenticated': request.user.is_authenticated,  # Pass this to check if the user is logged in
        'initial_quantity': initial_quantity, 
    })

@check_blacklisted
@login_required
def chat_with_vendor(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.user == product.vendor:
        return redirect('shop:product_detail', product_id=product.id)
    
    chat_messages = ChatMessage.objects.filter(
        product=product
    ).filter(
        Q(sender=request.user, receiver=product.vendor) | 
        Q(sender=product.vendor, receiver=request.user)
    ).order_by('created_at')

    return render(request, 'shop/chat_with_vendor.html', {
        'product': product,
        'chat_messages': chat_messages,
    })


def category_products(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    products = Product.objects.filter(categories=category, status='approved')
    categories = Category.objects.all().order_by('name')
    
    print(f"Category ID: {category_id}")
    print(f"Category Name: {category.name}")
    print(f"Number of Products: {products.count()}")
    
    context = {
        'category': category,
        'products': products,
        'categories': categories,
    }
    return render(request, 'shop/category_products.html', context)


def get_cart(user):
    """Retrieve or create a cart for the user."""
    cart, created = Cart.objects.get_or_create(user=user)
    
    return cart

@check_blacklisted
@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    # Prevent vendors from adding their own products to the cart
    if request.user == product.vendor:
        return JsonResponse({
            "status": "error", 
            "message": "You cannot purchase your own product."
        }, status=400)
    
    
    if request.method == "POST":
        quantity = int(request.POST.get("quantity", 1))
        print(f"Adding quantity: {quantity} for product {product.name}")

        cart = get_cart(request.user)
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)

        cart_item.quantity = quantity
        cart_item.save()
        # messages.success(request, f"{product.name} has been added to your cart.")
        cart_count = CartItem.objects.filter(cart=cart).count()

        return JsonResponse({"status": "success", "cart_count": cart_count})
    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)

@check_blacklisted
@login_required
def view_cart(request):
    """Display cart items."""
    cart = get_cart(request.user)  
    cart_items = CartItem.objects.filter(cart=cart)

    for item in cart_items:
        item.total_price = item.product.price * item.quantity

    cart_total = sum(item.total_price for item in cart_items)


    return render(request, "shop/cart.html", {"cart_items": cart_items, "cart_total": cart_total})

@check_blacklisted
@login_required
def update_cart(request, item_id):
    """Update the quantity of a cart item."""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    if request.method == "POST":
        quantity = int(request.POST.get("quantity", 1))
        if quantity <= 0:
            cart_item.delete()
        else:
            cart_item.quantity = min(quantity, cart_item.product.stock or 100)
            cart_item.save()
    return redirect('shop:cart')


@login_required
def remove_from_cart(request, item_id):
    """Remove an item from the cart."""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    return redirect('shop:cart')

@check_blacklisted
@login_required
def checkout(request):
    """Handle checkout process."""
    if request.method == "POST":
        cart = get_cart(request.user)
        cart_items = CartItem.objects.filter(cart=cart)

        if not cart_items:
            return redirect('shop:cart')

        # Extract form data
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        country = request.POST.get('country', '').strip()
        state = request.POST.get('state', '').strip()
        postal_code = request.POST.get('postal_code', '').strip()

        # Validate required fields
        if not first_name or not last_name or not country or not state or not postal_code:
            return redirect('shop:cart')  # Redirect back if validation fails

        # Create Checkout instance
        checkout = Checkout.objects.create(
            user=request.user,
            first_name=first_name,
            last_name=last_name,
            email=request.user.email or "unknown@example.com",
            address=f"{country}, {state}",
            city=state,
            postal_code=postal_code,
            phone=request.user.profile.phone if hasattr(request.user, 'profile') else "N/A",
        )

        return redirect('shop:order_confirmation' )

    return redirect('shop:cart')


from decimal import Decimal
@login_required
def order_confirmation(request):
    # Get the user's cart
    cart = Cart.objects.get(user=request.user)
    cart_items = CartItem.objects.filter(cart=cart)

    if not cart_items:
        return redirect('shop:cart')

    # Get the latest checkout instance for the user
    try:
        checkout = Checkout.objects.filter(user=request.user).latest('created_at')
    except Checkout.DoesNotExist:
        return redirect('shop:cart')

    # Calculate subtotal (sum of Decimal values)
    subtotal = sum(item.product.price * item.quantity for item in cart_items)
    
    # Define shipping and tax as Decimal
    shipping = Decimal('4.00')  # Convert float to Decimal
    tax = Decimal('0.00')       # Convert float to Decimal
    grand_total = subtotal + shipping + tax

    # Context to pass to the template
    context = {
        'checkout': checkout,
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping': shipping,
        'tax': tax,
        'grand_total': grand_total,
        'message': 'Please review your order before confirmation.',
    }

    return render(request, 'shop/checkout.html', context)


import logging
from django.db import transaction
from django.http import HttpResponse
import requests
import uuid
import json

# Set up logging
logger = logging.getLogger(__name__)
@login_required
def place_order(request):
    if request.method == "POST":
        logger.info(f"Place order initiated for user: {request.user}")
        cart = get_cart(request.user)
        cart_items = CartItem.objects.filter(cart=cart)

        if not cart_items:
            logger.warning("Cart is empty, redirecting to cart.")
            return redirect('shop:cart')

        try:
            checkout = Checkout.objects.filter(user=request.user).latest('created_at')
            logger.info(f"Checkout retrieved: {checkout}")
        except Checkout.DoesNotExist:
            logger.error("No checkout found, redirecting to cart.")
            return redirect('shop:cart')

        subtotal = sum(item.product.price * item.quantity for item in cart_items)
        shipping = Decimal('4.00')
        grand_total = subtotal + shipping

        payment_method = request.POST.get('payment_method')
        logger.info(f"Payment method selected: {payment_method}")

        valid_payment_methods = [key for key, value in Order.Payment_Method]
        if payment_method not in valid_payment_methods:
            logger.error(f"Invalid payment method: {payment_method}. Valid options: {valid_payment_methods}")
            return redirect('shop:order_confirmation')

        # Store data in session
        request.session['grand_total'] = float(grand_total)
        request.session['cart_items'] = [
            {
                'product_id': item.product.id,
                'product_name': item.product.name,
                'price': float(item.product.price),
                'quantity': item.quantity,
                'total_price': float(item.product.price * item.quantity)
            } for item in cart_items
        ]
        logger.info("Session data stored: grand_total and cart_items")

        if payment_method == 'Khalti':
            # Directly initiate Khalti payment
            logger.info("Initiating Khalti payment directly")
            transaction_uuid = uuid.uuid4()
            amount = int(grand_total * 100)  # Convert to paisa

            payload = {
                "return_url": request.build_absolute_uri('/khalti_verify'),
                "website_url": "http://localhost:8000",  # Replace with your actual website URL
                "amount": amount,
                "purchase_order_id": str(transaction_uuid),
                "purchase_order_name": "Order Payment",
                "customer_info": {
                    "name": request.user.full_name,
                    "email": request.user.email,
                    "phone": "9800000001"  # Replace with actual user phone
                }
            }

            headers = {
                 'Authorization': 'Key 28808af5b2f74228b7da6ba0a27b1e7e',  # Corrected to a string
                'Content-Type': 'application/json',
            }

            url = "https://a.khalti.com/api/v2/epayment/initiate/"
            try:
                response = requests.post(url, headers=headers, json=payload)
                logger.info(f"Khalti API response: {response.status_code} - {response.text}")
                if response.status_code == 200:
                    new_res = json.loads(response.text)
                    payment_url = new_res.get('payment_url')
                    if payment_url:
                        logger.info(f"Redirecting to Khalti payment URL: {payment_url}")
                        return redirect(payment_url)
                    else:
                        logger.error("No payment_url in Khalti response")
                        return redirect('shop:cart')
                else:
                    logger.error(f"Khalti API failed with status {response.status_code}: {response.text}")
                    return redirect('shop:cart')
            except Exception as e:
                logger.error(f"Error during Khalti API call: {str(e)}")
                return redirect('shop:cart')
        else:
            try:
                with transaction.atomic():
                    for item in cart_items:
                        Order.objects.create(
                            user=request.user,
                            product=item.product,
                            price=item.product.price,
                            quantity=item.quantity,
                            total_price=item.product.price * item.quantity,
                            payment_method=payment_method,
                            status="pending",
                        )
                    cart_items.delete()
                    logger.info("Cart cleared successfully.")
            except Exception as e:
                logger.error(f"Failed to create orders: {str(e)}")
                return redirect('shop:order_confirmation')

            return render(request, 'shop/checkout.html', {
                'message': 'Order has been placed successfully!',
                'checkout': checkout,
                'grand_total': grand_total,
            })

    logger.warning("Non-POST request to place_order, redirecting to cart.")
    return redirect('shop:cart')

from django.core.mail import send_mail
@login_required
def khalti_verify(request):
    if request.method == 'GET':
        pidx = request.GET.get('pidx')
        if not pidx:
            logger.error("No pidx provided for Khalti verification")
            return redirect('shop:cart')

        # Verify payment with Khalti
        headers = {
            'Authorization': 'Key 28808af5b2f74228b7da6ba0a27b1e7e',  # Replace with your Khalti secret key
            'Content-Type': 'application/json',
        }
        url = "https://a.khalti.com/api/v2/epayment/lookup/"
        payload = {"pidx": pidx}
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 200:
            result = json.loads(response.text)
            if result.get('status') == 'Completed':
                # Payment successful, create orders
                cart_items = request.session.get('cart_items', [])
                grand_total = Decimal(request.session.get('grand_total', 0))
                order_list = []

                try:
                    with transaction.atomic():
                        for item in cart_items:
                            product = Product.objects.get(id=item['product_id'])  # Fetch product using ID
                            Order.objects.create(
                                user=request.user,
                                product=product,
                                price=Decimal(item['price']),
                                quantity=item['quantity'],
                                total_price=Decimal(item['total_price']),
                                payment_method='khalti',
                                status="pending",
                            )
                            order_list.append(f"- {product.name} x {item['quantity']} (${item['total_price']})")
                        # Clear cart (assuming cart_items.delete() clears the cart in DB)
                        CartItem.objects.filter(cart=get_cart(request.user)).delete()
                        logger.info("Cart cleared successfully after Khalti payment.")

                        # Clean up session
                        del request.session['cart_items']
                        del request.session['grand_total']


                        # **Send Order Confirmation Email**
                    # Send Order Confirmation Email
                    user_email = request.user.email
                    if not user_email:
                        logger.error("User email is not set.")
                        messages.warning(request, "Order placed, but email confirmation failed due to missing email.")
                    else:
                        total_paid = round(grand_total, 2)
                        subject = "Order Confirmation - Payment Successful"
                        message = f"""
                        Dear {request.user.full_name},

                        Your payment via Khalti was successful!

                        **Order Details:**
                        {chr(10).join(order_list)}

                        **Total Paid:** ${total_paid}

                        Your order is now being processed. Thank you for shopping with us!

                        Regards, 
                        Your Store Team
                        """
                        try:
                            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user_email], fail_silently=False)
                            logger.info(f"Order confirmation email sent to {user_email}")
                        except Exception as e:
                            logger.error(f"Failed to send email: {str(e)}")
                            messages.warning(request, "Order placed, but email confirmation failed.")

                    messages.success(request, 'Order has been placed successfully via Khalti!')
                    return redirect('shop:order_list')
                except Exception as e:
                    logger.error(f"Failed to create orders after Khalti payment: {str(e)}")
                    return redirect('shop:order_confirmation')
            else:
                logger.error(f"Khalti payment not completed: {result}")
                return redirect('shop:cart')
        else:
            logger.error(f"Khalti verification failed: {response.text}")
            return redirect('shop:cart')

    return HttpResponse("Invalid Request")


def about(request):
    return render(request, 'about.html')

def contact(request):
     form = ContactForm()
     if request.method == "POST":
            form = ContactForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Your message has been sent successfully!")
                return redirect("shop:home")  
     return render(request, 'contact.html',{"form": form})

from django.db.models import Max
@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    bid_orders = BidOrder.objects.filter(user=request.user).select_related('auction', 'product').order_by('-ordered_at')

# Debugging
    logger.info(f"Bid Orders for {request.user}: {bid_orders.count()} found")
    for bid in bid_orders:
        logger.info(f"Bid Order: {bid}, Auction: {bid.auction}, Status: {bid.status}")
        
    # Fetch auction participation history
    auction_data = (
        Bid.objects
        .filter(bidder=request.user)  # Filter bids by the logged-in user
        .select_related('auction', 'auction__product')  # Optimize query by joining with Auction and Product
        .values('auction')  # Group by auction
        .annotate(user_highest_bid=Max('amount'))  # Get the highest bid for each auction
        .order_by('-auction__end_time')  # Order by auction end time
    )

    # Fetch full auction details for each unique auction
    auctions = []
    for data in auction_data:
        auction = Auction.objects.get(id=data['auction'])
        payment_url = f"/pay/{auction.id}/" 
        auctions.append({
            'auction': auction,
            'user_highest_bid': data['user_highest_bid'],
            'payment_url': payment_url,

        })
    return render(request, 'shop/order_list.html', {
        'orders': orders,
        'bid_orders': bid_orders,
        'auctions': auctions,  # Pass the full auction data to the template
    })

@login_required
def pay_auction(request, auction_id):
    """Handle payment for a won auction via Khalti."""
    auction = get_object_or_404(Auction, id=auction_id)
    bid_order = get_object_or_404(BidOrder, auction=auction, user=request.user)

    # Validate payment conditions
    if auction.highest_bidder != request.user:
        messages.error(request, "You are not the winning bidder for this auction.")
        return redirect('shop:order_list')
    
    if auction.is_active:
        messages.error(request, "Auction is still active. Payment unavailable.")
        return redirect('shop:order_list')
    
    if bid_order.status != 'pending':
        messages.info(request, "This auction has already been paid or processed.")
        return redirect('shop:order_list')

    # Convert amount to paisa (minimum 1000 paisa = Rs 10)
    amount = int(bid_order.bid_amount * 100)
    if amount < 1000:
        messages.error(request, "Minimum payment amount is Rs 10.")
        return redirect('shop:order_list')

    # Prepare Khalti payload
    transaction_uuid = str(uuid.uuid4())
    user_profile = getattr(request.user, 'profile', None)
    
    payload = {
        "return_url": request.build_absolute_uri(reverse('shop:khalti_verify_auction')),
        "website_url": "http://localhost:8000",
        "amount": amount,
        "purchase_order_id": transaction_uuid,
        "purchase_order_name": f"Auction-{auction.id}-{bid_order.id}",
        "customer_info": {
            "name": "Customer",
            "email": request.user.email or "customer@example.com",
            "phone": user_profile.phone if user_profile else "9800000000"
        }
    }

    headers = {
        'Authorization': f'Key {KHALTI_SECRET_KEY}',
        'Content-Type': 'application/json',
    }

    # Use the same Khalti endpoint as regular payments
    url = "https://a.khalti.com/api/v2/epayment/initiate/"
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()  # Raises exception for 4XX/5XX status codes
        
        payment_data = response.json()
        if not payment_data.get('payment_url'):
            raise ValueError("No payment URL in response")
            
        # Store critical data in session
        request.session['auction_payment'] = {
            'auction_id': auction.id,
            'bid_order_id': bid_order.id,
            'transaction_uuid': transaction_uuid,
            'amount': amount,
        }
        
        return redirect(payment_data['payment_url'])
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Khalti API error: {str(e)}")
        messages.error(request, f"Payment initiation failed: {str(e)}")
        return redirect('shop:order_list')
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        messages.error(request, "Payment processing failed. Please try again.")
        return redirect('shop:order_list')
@login_required
def khalti_verify_auction(request):
    """Verify Khalti payment for an auction and update BidOrder."""
    if request.method != 'GET' or not request.GET.get('pidx'):
        messages.error(request, "Invalid payment verification request.")
        return redirect('shop:order_list')

    # Retrieve session data
    payment_data = request.session.get('auction_payment')
    if not payment_data:
        messages.error(request, "Payment session expired or invalid.")
        return redirect('shop:order_list')

    try:
        pidx = request.GET['pidx']
        bid_order = BidOrder.objects.get(
            id=payment_data['bid_order_id'],
            user=request.user,
            status='pending'
        )
        
        # Verify payment with Khalti
        headers = {
            'Authorization': f'Key {KHALTI_SECRET_KEY}',
            'Content-Type': 'application/json',
        }
        url = "https://a.khalti.com/api/v2/epayment/lookup/"
        payload = {"pidx": pidx}
        
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        
        verification_data = response.json()
        
        if verification_data.get('status') != 'Completed':
            raise ValueError("Payment not completed")
            
        # Payment successful - update bid order
        if verification_data.get('status') == 'Completed':
            bid_order.status = 'paid'  # Make sure this matches your STATUS_CHOICES
            bid_order.payment_status = 'Khalti'
            bid_order.save()
        
        # Send confirmation email
        try:
            send_mail(
                subject=f"Auction Payment Confirmation - Order #{bid_order.id}",
                message=render_to_string('emails/auction_payment.txt', {
                    'user': request.user,
                    'bid_order': bid_order,
                }),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[request.user.email],
                fail_silently=False
            )
        except Exception as e:
            logger.error(f"Failed to send confirmation email: {str(e)}")
        
        # Clean up session
        del request.session['auction_payment']
        
        messages.success(request, "Payment successful! Your order is being processed.")
        return redirect('shop:order_list')
        
    except BidOrder.DoesNotExist:
        messages.error(request, "Order not found or already processed.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Khalti verification error: {str(e)}")
        messages.error(request, "Payment verification failed. Please contact support.")
    except Exception as e:
        logger.error(f"Payment processing error: {str(e)}")
        messages.error(request, "Payment processing failed. Please contact support.")
    
    return redirect('shop:order_list')


from django.urls import reverse
@login_required
def request_refund(request, order_id):
    order = Order.objects.get(id=order_id, user=request.user)
    if request.method == 'POST':
        reason = request.POST.get('reason')
        if not RefundRequest.objects.filter(order=order).exists():
            RefundRequest.objects.create(
                order=order,
                user=request.user,
                reason=reason
            )
            messages.success(request, "Refund request submitted successfully!")
        else:
            messages.error(request, "A refund request for this order already exists.")
        return redirect('shop:order_list')
    return render(request, 'shop/request_refund.html', {'order': order})



# View for ongoing (live) auctions
def auction_list(request):
    auctions = Auction.objects.filter(
        is_active=True,
        start_time__lte=timezone.now(),  # Started already
        end_time__gt=timezone.now(),
        product__status='approved'
    ).select_related('product').order_by('end_time')
    
    print(auctions)

    context = {
        'auctions': auctions,
        'auction_type': 'live',  # Used in template logic
    }
    return render(request, 'shop/auction_list.html', context)

# View for future (upcoming) auctions
def auction_upcoming(request):
    auctions = Auction.objects.filter(
        start_time__gt=timezone.now(),  # Starts in the future
        product__status='approved'
    ).select_related('product').order_by('start_time')
    
    context = {
        'auctions': auctions,
        'auction_type': 'upcoming',
    }
    return render(request, 'shop/auction_list.html', context)

# View for past auctions
def auction_past(request):
    auctions = Auction.objects.filter(
        end_time__lte=timezone.now(),  # Ended
        product__status='approved'
    ).select_related('product').prefetch_related('bids').order_by('-end_time')
    
    context = {
        'auctions': auctions,
        'auction_type': 'past',
    }
    return render(request, 'shop/auction_list.html', context)

from user.models import KYCVerification

# View to view details and place a bid on an auction
@login_required
@check_blacklisted
def auction_detail(request, auction_id):
    auction = get_object_or_404(Auction, id=auction_id, product__status='approved')
    product = auction.product
    
    if not auction.is_active or timezone.now() >= auction.end_time:
        auction.is_active = False
        auction.notify_winner()
        auction.save()
        messages.info(request, "This auction has ended.")
        return redirect('shop:auction_list')

    auction.notify_ending_soon()

    # Check KYC verification status
    can_bid = request.user.kyc_verified or request.user.role == 'superadmin'

    if request.method == 'POST':
        form = BidForm(request.POST)
        if form.is_valid():
            if not can_bid:
                messages.error(request, "You are not KYC verified and cannot place a bid.")
            else:
                bid_amount = form.cleaned_data['amount']
                if (auction.highest_bid and bid_amount <= auction.highest_bid) or bid_amount <= auction.starting_bid:
                    messages.error(request, "Your bid must be higher than the current highest bid or starting bid.")
                elif request.user == product.vendor:
                    messages.error(request, "You cannot bid on your own auction.")
                else:
                    bid = Bid(auction=auction, bidder=request.user, amount=bid_amount)
                    bid.save()  # Triggers outbid notification via Bid.save()
                    messages.success(request, "Your bid has been placed successfully!")
                    return redirect('shop:auction_detail', auction_id=auction.id)
        else:
            messages.error(request, "Invalid bid amount.")
    else:
        form = BidForm()

    context = {
        'auction': auction,
        'product': product,
        'form': form,
        'bids': auction.bids.order_by('-amount')[:5], 
        'can_bid': can_bid, # Show top 5 bids
    }
    return render(request, 'shop/auction_detail.html', context)



@login_required
def notifications(request):
    filter_type = request.GET.get('filter', 'all')

    notifications = Notification.objects.filter(user=request.user, is_read=False).select_related('auction')

    # Apply filter based on notification_type
    if filter_type != 'all':
        notifications = notifications.filter(notification_type=filter_type)

    if request.method == 'POST' and 'mark_read' in request.POST:
        notifications.update(is_read=True)
        return redirect('shop:notifications')

    # Check active auctions for ending soon notifications
    active_auctions = Auction.objects.filter(is_active=True, end_time__gt=timezone.now())
    for auction in active_auctions:
        auction.notify_ending_soon()  # This now avoids duplicates

    context = {
            'notifications': notifications,
            'current_filter': filter_type,  # Pass current filter to template
               }
    return render(request, 'shop/notifications.html', context)


@login_required
@check_blacklisted
def subscribe_to_price_drop(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if product.product_type == Product.AUCTION:
        messages.error(request, "Price drop alerts are not available for auction products.")
        return redirect('shop:product_detail', product_id=product.id)
    if request.method == 'POST':
        subscription, created = PriceDropSubscription.objects.get_or_create(
            user=request.user,
            product=product,
            defaults={'last_notified_price': product.price}  # Use price directly since discount is removed
        )
        if created:
            messages.success(request, f"You’ll be notified if the price of {product.name} drops!")
        else:
            messages.info(request, f"You’re already subscribed to price drop alerts for {product.name}.")
    return redirect('shop:product_detail', product_id=product.id)