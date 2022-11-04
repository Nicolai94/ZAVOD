import json

from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .models import Messages, Room
from django.contrib.auth.models import User


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat-%s' % self.room_name

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        username = data['username']
        room = data['room']
        mtype = data['type']

        await self.save_message(username, room, message, mtype)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': mtype,
                'message': message,
                'username': username,
                'room': room,


            }
        )

    async def chat_message(self, event):
        message = event['message']
        username = event['username']
        room = event['room']

        await self.send(text_data=json.dumps({
            'message': message,
            'username': username,
            'room': room,
        }))

    @sync_to_async
    def save_message(self, username, room, message, mtype):
        user = User.objects.get(username=username)
        room = Room.objects.get(slug=room)
        Messages.objects.create(user=user, room=room, content=message, type=mtype)

    async def chat_photo(self, event):
        await self.send(text_data=json.dumps(event))
