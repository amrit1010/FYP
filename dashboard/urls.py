from django.urls import path
from .views import *

app_name = 'dashboard'

urlpatterns = [
    path('', vendor_dashboard, name='vendor_dashboard'),
    path('profile/', profile, name = 'vendor-profile'),
    path('profile/edit/',profile_edit, name='profile_edit'),
    path('profile/change-password/', change_password, name='change_password'),
    path('vendor/products/', vendor_products, name='vendor_products'),
    path('vendor/add-product/',add_product, name='add_product'),
    path('vendor/edit-product/<int:product_id>/', edit_product, name='edit_product'),
    path('vendor/remove-product/<int:product_id>/', remove_product, name='remove_product'),
    path('vendor/orders/',vendor_orders, name='vendor_orders'),
    path('vendor/order/<int:order_id>/update/',vendor_order_update, name='vendor_order_update'),
    path('message/', message, name = 'message'),

    path('messages/',vendor_messages, name='vendor_messages'),
    path('messages/<int:message_id>/', reply_message, name='reply_message'),


]
