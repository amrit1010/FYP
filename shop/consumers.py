import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.product_id = self.scope['url_route']['kwargs']['product_id']
        self.user = self.scope['user']
        self.chat_group_name = f'chat_product_{self.product_id}'
        logger.info(f"WebSocket connect attempt for product_id: {self.product_id}")

        if await self.is_valid_user():
            logger.info(f"User {self.user} connected to group {self.chat_group_name}")
            await self.channel_layer.group_add(
                self.chat_group_name,
                self.channel_name
            )
            await self.accept()
        else:
            logger.warning(f"User {self.user} not authorized for product {self.product_id}")
            await self.close()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.chat_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        logger.info(f"Received message: {message} from user {self.user}")

        saved_message = await self.save_message(message)

        # Send to product group (buyer and vendor in chat)
        await self.channel_layer.group_send(
            self.chat_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender_id': self.user.id,
                'sender_name': self.user.full_name,
                'timestamp': saved_message.created_at.isoformat(),
            }
        )

        # Send to vendor's group (for vendor_messages.html)
        vendor_id = await self.get_vendor_id()
        await self.channel_layer.group_send(
            f'vendor_messages_{vendor_id}',
            {
                'type': 'vendor_message',
                'message': message,
                'sender_id': self.user.id,
                'sender_name': self.user.full_name,
                'product_id': self.product_id,
                'product_name': saved_message.product.name,
                'message_id': saved_message.id,
                'timestamp': saved_message.created_at.isoformat(),
            }
        )

    async def chat_message(self, event):
        logger.info(f"Sending message to client: {event['message']}")
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
            'timestamp': event['timestamp'],
        }))

    @database_sync_to_async
    def is_valid_user(self):
        from shop.models import ChatMessage, Product
        from core.models import CustomUser
        try:
            product = Product.objects.get(id=self.product_id)
            return (self.user == product.vendor or
                    ChatMessage.objects.filter(
                        product=product,
                        sender=self.user
                    ).exists() or
                    self.user.is_authenticated)
        except Product.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, content):
        from shop.models import ChatMessage, Product
        from core.models import CustomUser
        product = Product.objects.get(id=self.product_id)
        receiver = (ChatMessage.objects.filter(
            product=product, receiver=product.vendor
        ).first().sender if self.user == product.vendor else product.vendor)
        return ChatMessage.objects.create(
            sender=self.user,
            receiver=receiver,
            product=product,
            message=content
        )

    @database_sync_to_async
    def get_vendor_id(self):
        from shop.models import Product
        product = Product.objects.get(id=self.product_id)
        return product.vendor.id