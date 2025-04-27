import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)

class VendorMessagesConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        self.group_name = f'vendor_messages_{self.user.id}'
        logger.info(f"Vendor WebSocket connect attempt for user_id: {self.user.id}")

        if self.user.is_authenticated:
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            await self.accept()
            logger.info(f"Vendor {self.user} connected to group {self.group_name}")
        else:
            logger.warning(f"Unauthorized connection attempt for user: {self.user}")
            await self.close()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        logger.info(f"Vendor {self.user} disconnected from group {self.group_name}")

    async def vendor_message(self, event):
        logger.info(f"Sending message to vendor {self.user}: {event['message']}")
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
            'product_id': event['product_id'],
            'product_name': event['product_name'],
            'message_id': event['message_id'],
            'timestamp': event['timestamp'],
        }))