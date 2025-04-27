from django.urls import path
from .views import *

app_name = 'shop'

urlpatterns = [
    path('', home, name='home'),
    path('product/<int:product_id>/',product_detail, name='product_detail'),
    path('category/<int:category_id>/', category_products, name='category_products'),
    path('product/<int:product_id>/chat/',chat_with_vendor, name='chat_with_vendor'),
    path('cart/', view_cart, name='cart'),
    path('cart/add/<int:product_id>/', add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', update_cart, name='update_cart'),
    path('cart/remove/<int:item_id>/', remove_from_cart, name='remove_from_cart'),
    path('checkout/', checkout, name='checkout'),
    path('order-confirmation/', order_confirmation, name='order_confirmation'),
    path('place-order/', place_order, name='place_order'),
    path('khalti_verify', khalti_verify, name='khalti_verify'),
    path('contact/', contact, name='contact'),
    path('about/', about, name='about'),
    path('orders/', order_list, name='order_list'),
    path('order/<int:order_id>/refund/', request_refund, name='request_refund'),

    path('search/', search_view, name="search"),

    path('auctions/live/', auction_list, name='auction_list'),
    path('auctions/upcoming/',auction_upcoming, name='auction_upcoming'),
    path('auctions/past/',auction_past, name='auction_past'),
    path('auction/<int:auction_id>/', auction_detail, name='auction_detail'),

    path('notifications/', notifications, name='notifications'),
    path('product/<int:product_id>/subscribe/', subscribe_to_price_drop, name='subscribe_to_price_drop'),


    path('pay_auction/<int:auction_id>/', pay_auction, name='pay_auction'),
    path('khalti_verify_auction/', khalti_verify_auction, name='khalti_verify_auction'),

]
