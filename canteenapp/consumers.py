from channels.generic.websocket import AsyncWebsocketConsumer
import json
from .models import Menu,Item,Cart,CustomUser,Prices
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.conf import settings
from django.contrib.auth.models import AnonymousUser 

class MenuConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add('menu_group', self.channel_name)
        await self.accept()
        await self.send_current_menu()

    async def disconnect(self, code):
        await self.channel_layer.group_discard('menu_group', self.channel_name)
        print("Disconnected from WebSocket")

    @database_sync_to_async
    def get_menus(self):
        return Menu.objects.all()

    async def send_current_menu(self):
        try:
            menus = await self.get_menus()
            menu_list = [
                {
                    'menu_id': menu.id,
                    'menu_name': menu.menu_name,
                    'menu_picture': menu.menu_image.url if menu.menu_image else None
                }
                for menu in menus
            ]
            await self.send(text_data=json.dumps({'data': menu_list}))
        except Exception as e:
            print(f"Error sending current menu: {e}")

    async def receive(self, text_data=None, bytes_data=None):
        if text_data:
            text_data_json = json.loads(text_data)
            message = text_data_json.get('message')

    async def menu_update(self, event):
        await self.send_current_menu()

class AllItemsConsumer(AsyncWebsocketConsumer): 
    async def connect(self):
        self.user = self.scope['user'] 
        await self.channel_layer.group_add('allitems_group', self.channel_name)
        await self.accept()
        await self.send_current_items() 

    async def disconnect(self, code):
        await self.channel_layer.group_discard('allitems_group', self.channel_name)

    @database_sync_to_async
    def get_items_with_cart(self):
        items = Item.objects.select_related('menu', 'submenu').all()
        cart_items = Cart.objects.filter(user=self.user) if not isinstance(self.user, AnonymousUser) else []
        cart_dict = {cart_item.item_id: cart_item.quantity for cart_item in cart_items}
        
        return items, cart_dict

    async def send_current_items(self):
        try:
            items, cart_dict = await self.get_items_with_cart()
            item_list = [
                {
                    'item_id': item.id,
                    'item_name': item.item_name,
                    'menu': item.menu.menu_name if item.menu else None,
                    'submenu': item.submenu.sub_menu_name if item.submenu else None,
                    'description': item.description,
                    'type': item.type,
                    'price': float(item.price), 
                    'is_available': item.is_available,
                    'preparation_time': item.preparation_time,
                    'item_image': item.item_image.url if item.item_image else None,
                    'in_cart': item.id in cart_dict,  
                    'quantity': cart_dict.get(item.id, 0) 
                }
                for item in items
            ]
            await self.send(text_data=json.dumps({'data': item_list}))
        except Exception as e:
            print(f"Error sending items: {e}")

    async def item_update(self, event): 
        await self.send_current_items()

class CartItemConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add('cartitem_group', self.channel_name)
        await self.accept()
        await self.send_current_cart_items()
    async def disconnect(self, code):
        await self.channel_layer.group_discard('cartitem_group', self.channel_name)
        print("Disconnected from WebSocket")
    @database_sync_to_async
    def get_cart_items(self, user_email):
        try:
            user = CustomUser.objects.get(email=user_email)
            return list(Cart.objects.filter(user=user).select_related('item').filter(item__is_available=True).values(
                'item__id',
                'item__item_name',
                'item__price',
                'item__description',
                'item__item_image',
                'item__type',
                'quantity',
                'item__preparation_time'
            ))
        except CustomUser.DoesNotExist:
            return []

    async def send_current_cart_items(self):
        user = self.scope.get('user')
        if user is not None and user.is_authenticated:
            user_email = user.email
            try:
                cart_items = await self.get_cart_items(user_email)
                cart_list = [
                    {
                        'id': cartitem['item__id'],
                        'item_name': cartitem['item__item_name'],
                        'price': float(cartitem['item__price']),
                        'description': cartitem['item__description'],
                        'item_image': (
                            f"{settings.MEDIA_URL}{cartitem['item__item_image']}" if cartitem['item__item_image'] else None
                        ),
                        'type': cartitem['item__type'],
                        'quantity': cartitem['quantity'],
                        'preparation_time': cartitem['item__preparation_time'],
                    }
                    for cartitem in cart_items
                ]
                await self.send(text_data=json.dumps({'data': cart_list}))
            except Exception as e:
                print(f"Error sending items: {e}")
                await self.send(text_data=json.dumps({'data': [], 'error': 'Error retrieving cart items.'}))
        else:
            print("User is not authenticated or user is None, unable to send cart items.")
            await self.send(text_data=json.dumps({'data': [], 'error': 'User not authenticated.'}))

    async def cart_update(self, event):
        await self.send_current_cart_items()

class AdditionalPricesConsumer(AsyncWebsocketConsumer): 
    async def connect(self):
        self.user = self.scope['user'] 
        await self.channel_layer.group_add('addprices_group', self.channel_name)
        await self.accept()
        await self.send_current_addprices() 

    async def disconnect(self, code):
        await self.channel_layer.group_discard('addprices_group', self.channel_name)

    @database_sync_to_async
    def get_add_prices(self):
        return Prices.objects.all()

    async def send_current_addprices(self):
        try:
            all_prices = await self.get_add_prices()
            delivery_type = self.user.delivery_type 
            filtered_prices = self.filter_prices(all_prices, delivery_type)

            add_prices_list = [
                {
                    'price_type': price.price_type,
                    'value_type': price.value_type,
                    'value': float(price.value),
                }
                for price in filtered_prices
            ]
            await self.send(text_data=json.dumps({'data': add_prices_list}))
        except Exception as e:
            print(f"Error sending additional prices: {e}")

    async def addprices_update(self, event):
        await self.send_current_addprices()

    def filter_prices(self, prices, delivery_type):
        filtered_prices = []
        common_prices = ['GST', 'Other', 'PlatFormFee'] 

        for price in prices:
            if price.price_type in common_prices:
                filtered_prices.append(price)
            elif delivery_type == 'delivery':
                if price.price_type in ['Delivery', 'Packaging']:
                    filtered_prices.append(price)
            elif delivery_type == 'dining':
                if price.price_type == 'Service':
                    filtered_prices.append(price)
            elif delivery_type == 'pickup':
                if price.price_type == 'Packaging':
                    filtered_prices.append(price)
        return filtered_prices

class SearchItemsConsumer(AsyncWebsocketConsumer): 
    async def connect(self):
        self.user = self.scope['user'] 
        await self.channel_layer.group_add('search_items_group', self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard('search_items_group', self.channel_name)

    @database_sync_to_async
    def get_filtered_items(self, search_term):
        items = Item.objects.select_related('menu', 'submenu').filter(item_name__icontains=search_term)
        cart_items = Cart.objects.filter(user=self.user) if not isinstance(self.user, AnonymousUser) else []
        cart_dict = {cart_item.item_id: cart_item.quantity for cart_item in cart_items}
        
        return items, cart_dict

    async def send_search_update(self):
        await self.send(text_data=json.dumps({'refresh_search': True}))

    async def receive(self, text_data):
        data = json.loads(text_data)
        search_term = data.get('search_term', '')
        await self.send_search_update()

    async def search_update(self, event): 
        search_term = event.get('search_term', '')
        cart_update_data = {
            'item_id': event.get('item_id'),
            'quantity': event.get('quantity'),
        }
        
        await self.send_search_update()