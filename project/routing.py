from django.urls import re_path
from shop import consumers
from dashboard import consumers as dashboard_consumers

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<product_id>\d+)/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'ws/vendor/messages/$', dashboard_consumers.VendorMessagesConsumer.as_asgi()),
]