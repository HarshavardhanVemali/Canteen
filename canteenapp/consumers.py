from channels.generic.websocket import AsyncWebsocketConsumer
import json
from .models import Menu,Item,Cart,CustomUser,Prices,Order
from django.utils import timezone
from datetime import timedelta
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
                    'quantity': cart_dict.get(item.id, 0),
                    'resturant_name':item.resturant.restaurant_name 
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


class AdminOrderConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope.get('user')
        if user and user.is_authenticated and user.role == 'admin':
            self.group_name = 'admin_group'
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
        print("Disconnected from WebSocket")

    async def admin_all_order(self, event):
        orders_data = await self.get_order_data()
        if orders_data:
            await self.send(text_data=json.dumps({
                'type':'admin_all_order',
                'orders':orders_data
            }))
    
    async def admin_new_order(self, event):
        orders_data = await self.get_order_data('confirmed')
        if orders_data:
            await self.send(text_data=json.dumps({
                'type':'admin_new_order',
                'orders':orders_data
            }))

    async def admin_cancelled_order(self, event):
        orders_data = await self.get_order_data('cancelled')
        if orders_data:
            await self.send(text_data=json.dumps({
                'type':'admin_cancelled_order',
                'orders':orders_data
            }))

    async def admin_delivered_order(self, event):
         orders_data = await self.get_order_data('delivered')
         if orders_data:
             await self.send(text_data=json.dumps({
                 'type':'admin_delivered_order',
                 'orders':orders_data
             }))
    @database_sync_to_async
    def get_order_data(self,status='None'):
        try:
            if not status or status=='None':
                orders = Order.objects.all().select_related('user', 'payment').prefetch_related('items', 'additional_charges').order_by('-created_at')
            else:
                orders = Order.objects.filter(status=status).select_related('user', 'payment').prefetch_related('items', 'additional_charges').order_by('-created_at')
            order_data = []

            for order in orders:
                order_items = []
                item_total_price = 0  
                for order_item in order.orderitem_set.all(): 
                    item = order_item.item
                    item_total_price += order_item.total_price 

                    order_items.append({
                        'item_name': item.item_name,
                        'quantity': order_item.quantity,
                        'price_at_order_time': str(order_item.price_at_purchase),  
                        'type': item.get_type_display(),
                        'is_available': item.is_available,
                        'item_image': item.item_image.url if item.item_image else None 
                    })
                additional_charges_data = []
                total_additional_charges = 0 
                for charge in order.additional_charges.all():
                    additional_charges_data.append({
                        'charge_type': charge.charge_type,
                        'value_type': charge.value_type,
                        'value': str(charge.value),
                        'calculated_value': str(charge.calculated_value)
                    })
                    total_additional_charges += charge.calculated_value  

                order_data.append({
                    'order_id': order.order_id,
                    'email': order.user.email,
                    'phone_number': order.user.phone_number,
                    'delivery_address':order.delivery_address,
                    'delivery_person': order.delivery_person.first_name if order.delivery_person else None,
                    'delivered_at': timezone.localtime(order.delivered_at).strftime('%d-%m-%Y %H:%M:%S') if order.delivered_at else None,
                    'cancelled_at': timezone.localtime(order.cancelled_at).strftime('%d-%m-%Y %H:%M:%S') if order.cancelled_at else None,
                    'cancel_reason':order.cancel_reason,
                    'customer': order.user.first_name + ' ' + order.user.last_name,
                    'total_price': str(order.total_price), 
                    'total_item_price': str(item_total_price),  
                    'total_additional_charges': str(total_additional_charges),  
                    'status': order.get_status_display(),
                    'delivery_type': order.delivery_type.capitalize(),
                    'created_at': timezone.localtime(order.created_at).strftime('%d-%m-%Y %H:%M:%S'),
                    'customer_status': order.customer_status.capitalize(),
                    'payment_method': order.payment.get_payment_method_display() if order.payment else '-',
                    'payment_amount': str(order.payment.amount) if order.payment else '-',
                    'transaction_id': order.payment.transaction_id if order.payment else '-',
                    'payment_status': order.payment.get_status_display() if order.payment else '-',
                    'payment_date': timezone.localtime(order.payment.payment_date).strftime('%d-%m-%Y %H:%M:%S') if order.payment and order.payment.payment_date else '-',
                    'items': order_items,
                    'additional_charges': additional_charges_data,
                    'restaurant_name':order.restaurant.restaurant_name,
                    'daily_sequence':order.daily_sequence,
                })
            return order_data
        except Order.DoesNotExist:
            return None
        
class RestaurantOrderConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope.get('user')
        if user and user.is_authenticated and user.role == 'restaurant':
            self.restaurant=CustomUser.objects.get(email=user.email)
            self.group_name = 'restaurant_group'
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()
            await self.send_all_orders()
        else:
            await self.close()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
        print("Disconnected from WebSocket")

    async def send_all_orders(self):
        orders_data = await self.get_order_data(restaurant=self.restaurant)
        if orders_data:
            await self.send(text_data=json.dumps({
                'type':'restaurant_all_order',
                'orders':orders_data
            }))


    async def restaurant_all_order(self, event):
         orders_data = await self.get_order_data(restaurant=self.restaurant)
         if orders_data:
             await self.send(text_data=json.dumps({
                 'type':'restaurant_all_order',
                 'orders':orders_data
             }))
    
    async def restaurant_new_order(self, event):
        orders_data = await self.get_order_data(status='confirmed',restaurant=self.restaurant)
        if orders_data:
            await self.send(text_data=json.dumps({
                'type':'restaurant_new_order',
                'orders':orders_data
            }))

    async def restaurant_cancelled_order(self, event):
        orders_data = await self.get_order_data(status='cancelled',restaurant=self.restaurant)
        if orders_data:
            await self.send(text_data=json.dumps({
                'type':'restaurant_cancelled_order',
                'orders':orders_data
            }))

    async def restaurant_delivered_order(self, event):
         orders_data = await self.get_order_data(status='delivered',restaurant=self.restaurant)
         if orders_data:
             await self.send(text_data=json.dumps({
                 'type':'restaurant_delivered_order',
                 'orders':orders_data
             }))

    @database_sync_to_async
    def get_order_data(self, status='None', restaurant=None):
        try:
            if not restaurant:
                return None

            if not status or status=='None':
                orders = Order.objects.filter(restaurant=restaurant).select_related('user', 'payment').prefetch_related('items', 'additional_charges').order_by('-created_at')
            else:
                orders = Order.objects.filter(status=status, restaurant=restaurant).select_related('user', 'payment').prefetch_related('items', 'additional_charges').order_by('-created_at')
            order_data = []

            for order in orders:
                order_items = []
                item_total_price = 0  
                for order_item in order.orderitem_set.all(): 
                    item = order_item.item
                    item_total_price += order_item.total_price 

                    order_items.append({
                        'item_name': item.item_name,
                        'quantity': order_item.quantity,
                        'price_at_order_time': str(order_item.price_at_purchase),  
                        'type': item.get_type_display(),
                        'is_available': item.is_available,
                        'item_image': item.item_image.url if item.item_image else None 
                    })
                additional_charges_data = []
                total_additional_charges = 0 
                for charge in order.additional_charges.all():
                    additional_charges_data.append({
                        'charge_type': charge.charge_type,
                        'value_type': charge.value_type,
                        'value': str(charge.value),
                        'calculated_value': str(charge.calculated_value)
                    })
                    total_additional_charges += charge.calculated_value  

                order_data.append({
                    'order_id': order.order_id,
                    'email': order.user.email,
                    'phone_number': order.user.phone_number,
                    'delivery_address':order.delivery_address,
                    'delivery_person': order.delivery_person.first_name if order.delivery_person else None,
                    'delivered_at': timezone.localtime(order.delivered_at).strftime('%d-%m-%Y %H:%M:%S') if order.delivered_at else None,
                    'cancelled_at': timezone.localtime(order.cancelled_at).strftime('%d-%m-%Y %H:%M:%S') if order.cancelled_at else None,
                    'cancel_reason':order.cancel_reason,
                    'customer': order.user.first_name + ' ' + order.user.last_name,
                    'total_price': str(order.total_price), 
                    'total_item_price': str(item_total_price),  
                    'total_additional_charges': str(total_additional_charges),  
                    'status': order.get_status_display(),
                    'delivery_type': order.delivery_type.capitalize(),
                    'created_at': timezone.localtime(order.created_at).strftime('%d-%m-%Y %H:%M:%S'),
                    'customer_status': order.customer_status.capitalize(),
                    'payment_method': order.payment.get_payment_method_display() if order.payment else '-',
                    'payment_amount': str(order.payment.amount) if order.payment else '-',
                    'transaction_id': order.payment.transaction_id if order.payment else '-',
                    'payment_status': order.payment.get_status_display() if order.payment else '-',
                    'payment_date': timezone.localtime(order.payment.payment_date).strftime('%d-%m-%Y %H:%M:%S') if order.payment and order.payment.payment_date else '-',
                    'items': order_items,
                    'additional_charges': additional_charges_data,
                    'restaurant_name':order.restaurant.restaurant_name,
                    'daily_sequence':order.daily_sequence,
                })
            return order_data
        except Order.DoesNotExist:
            return None
            
class DeliveryOrderConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope.get('user')
        if user and user.is_authenticated and user.role == 'delivery_person':
            self.delivery=CustomUser.objects.get(email=user.email)
            self.group_name = 'delivery_group'
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
        print("Disconnected from WebSocket")
    
    async def delivery_new_order(self, event):
        orders_data = await self.get_order_data(status='shipped',delivery=self.delivery)
        if orders_data:
            await self.send(text_data=json.dumps({
                'type':'delivery_new_order',
                'orders':orders_data
            }))

    async def delivery_delivered_order(self, event):
         orders_data = await self.get_order_data(status='delivered',delivery=self.delivery)
         if orders_data:
             await self.send(text_data=json.dumps({
                 'type':'delivery_delivered_order',
                 'orders':orders_data
             }))

    @database_sync_to_async
    def get_order_data(self, status='None', delivery=None):
        try:
            if not delivery:
                return None

            if not status or status=='None':
                orders = Order.objects.filter(delivery_person=delivery).select_related('user', 'payment').prefetch_related('items', 'additional_charges').order_by('-created_at')
            else:
                orders = Order.objects.filter(status=status, delivery_person=delivery).select_related('user', 'payment').prefetch_related('items', 'additional_charges').order_by('-created_at')
            order_data = []

            for order in orders:
                order_items = []
                item_total_price = 0  
                for order_item in order.orderitem_set.all(): 
                    item = order_item.item
                    item_total_price += order_item.total_price 

                    order_items.append({
                        'item_name': item.item_name,
                        'quantity': order_item.quantity,
                        'price_at_order_time': str(order_item.price_at_purchase),  
                        'type': item.get_type_display(),
                        'is_available': item.is_available,
                        'item_image': item.item_image.url if item.item_image else None 
                    })
                additional_charges_data = []
                total_additional_charges = 0 
                for charge in order.additional_charges.all():
                    additional_charges_data.append({
                        'charge_type': charge.charge_type,
                        'value_type': charge.value_type,
                        'value': str(charge.value),
                        'calculated_value': str(charge.calculated_value)
                    })
                    total_additional_charges += charge.calculated_value  

                order_data.append({
                    'order_id': order.order_id,
                    'email': order.user.email,
                    'phone_number': order.user.phone_number,
                    'delivery_address':order.delivery_address,
                    'delivery_person': order.delivery_person.first_name if order.delivery_person else None,
                    'delivered_at': timezone.localtime(order.delivered_at).strftime('%d-%m-%Y %H:%M:%S') if order.delivered_at else None,
                    'cancelled_at': timezone.localtime(order.cancelled_at).strftime('%d-%m-%Y %H:%M:%S') if order.cancelled_at else None,
                    'cancel_reason':order.cancel_reason,
                    'customer': order.user.first_name + ' ' + order.user.last_name,
                    'total_price': str(order.total_price), 
                    'total_item_price': str(item_total_price),  
                    'total_additional_charges': str(total_additional_charges),  
                    'status': order.get_status_display(),
                    'delivery_type': order.delivery_type.capitalize(),
                    'created_at': timezone.localtime(order.created_at).strftime('%d-%m-%Y %H:%M:%S'),
                    'customer_status': order.customer_status.capitalize(),
                    'payment_method': order.payment.get_payment_method_display() if order.payment else '-',
                    'payment_amount': str(order.payment.amount) if order.payment else '-',
                    'transaction_id': order.payment.transaction_id if order.payment else '-',
                    'payment_status': order.payment.get_status_display() if order.payment else '-',
                    'payment_date': timezone.localtime(order.payment.payment_date).strftime('%d-%m-%Y %H:%M:%S') if order.payment and order.payment.payment_date else '-',
                    'items': order_items,
                    'additional_charges': additional_charges_data,
                    'restaurant_name':order.restaurant.restaurant_name,
                    'daily_sequence':order.daily_sequence,
                })
            return order_data
        except Order.DoesNotExist:
            return None
        

"""     

        
class CustomerOrderConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope.get('user')
        if user and user.is_authenticated and user.role == 'delivery_person':
            self.delivery_person_id = user.id
            self.group_name = f'delivery_person_{self.delivery_person_id}'
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()
            await self.send_new_orders()
        else:
            await self.close()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
        print("Disconnected from WebSocket")

    @database_sync_to_async
    def get_new_orders(self, user_id):
        orders = Order.objects.filter(
            delivery_person_id=user_id,
            status='shipped'
        ).select_related('user', 'payment').prefetch_related('items', 'additional_charges').order_by('-created_at')
        order_data = []

        for order in orders:
            order_items = []
            item_total_price = 0
            for order_item in order.orderitem_set.all():
                item = order_item.item
                item_total_price += order_item.total_price

                order_items.append({
                    'item_name': item.item_name,
                    'quantity': order_item.quantity,
                    'price_at_order_time': str(order_item.price_at_purchase),
                    'type': item.get_type_display(),
                    'is_available': item.is_available,
                    'item_image': item.item_image.url if item.item_image else None
                })
            additional_charges_data = []
            total_additional_charges = 0
            for charge in order.additional_charges.all():
                additional_charges_data.append({
                    'charge_type': charge.charge_type,
                    'value_type': charge.value_type,
                    'value': str(charge.value),
                    'calculated_value': str(charge.calculated_value)
                })
                total_additional_charges += charge.calculated_value

            order_data.append({
                'order_id': order.order_id,
                'email': order.user.email,
                'phone_number': order.user.phone_number,
                'delivery_address': order.delivery_address,
                'customer': order.user.first_name + ' ' + order.user.last_name,
                'total_price': str(order.total_price),
                'total_item_price': str(item_total_price),
                'total_additional_charges': str(total_additional_charges),
                'status': order.get_status_display(),
                'created_at': timezone.localtime(order.created_at).strftime('%d-%m-%Y %H:%M:%S'),
                'cancelled_at':timezone.localtime(order.cancelled_at).strftime('%d-%m-%Y %H:%M:%S') if order.cancelled_at else None,
                'customer_status': order.customer_status.capitalize(),
                'payment_method': order.payment.get_payment_method_display() if order.payment else '-',
                'payment_amount': str(order.payment.amount) if order.payment else '-',
                'transaction_id': order.payment.transaction_id if order.payment else '-',
                'payment_status': order.payment.get_status_display() if order.payment else '-',
                'payment_date': timezone.localtime(order.payment.payment_date).strftime('%d-%m-%Y %H:%M:%S') if order.payment and order.payment.payment_date else '-',
                'items': order_items,
                'additional_charges': additional_charges_data,
                'restaurant_name': order.restaurant.restaurant_name,
                'daily_sequence':order.daily_sequence,
            })
        return order_data

    async def send_new_orders(self):
        if hasattr(self, 'delivery_person_id'):
            orders = await self.get_new_orders(self.delivery_person_id)
            await self.send(text_data=json.dumps({
                'type': 'new_orders',
                'orders': orders
            }))
        else:
            await self.send(text_data=json.dumps({'type': 'error', 'message': 'User is not authenticated or user is None, unable to send orders.'}))

    async def new_order(self, event):
        order_id = event['order_id']
        order = await self.get_order_data(order_id)
        if order:
            await self.send(text_data=json.dumps({
                'type':'new_order',
                'order':order
            }))
    @database_sync_to_async
    def get_order_data(self,order_id):
        try:
            order = Order.objects.filter(
                order_id=order_id,
                delivery_person_id=self.delivery_person_id,
                status='shipped'
            ).select_related('user', 'payment').prefetch_related('items', 'additional_charges').first()
            if not order:
                return None
            order_items = []
            item_total_price = 0
            for order_item in order.orderitem_set.all():
                item = order_item.item
                item_total_price += order_item.total_price

                order_items.append({
                    'item_name': item.item_name,
                    'quantity': order_item.quantity,
                    'price_at_order_time': str(order_item.price_at_purchase),
                    'type': item.get_type_display(),
                    'is_available': item.is_available,
                    'item_image': item.item_image.url if item.item_image else None
                })
            additional_charges_data = []
            total_additional_charges = 0
            for charge in order.additional_charges.all():
                additional_charges_data.append({
                    'charge_type': charge.charge_type,
                    'value_type': charge.value_type,
                    'value': str(charge.value),
                    'calculated_value': str(charge.calculated_value)
                })
                total_additional_charges += charge.calculated_value

            order_data = {
                'order_id': order.order_id,
                'email': order.user.email,
                'phone_number': order.user.phone_number,
                'delivery_address': order.delivery_address,
                'customer': order.user.first_name + ' ' + order.user.last_name,
                'total_price': str(order.total_price),
                'total_item_price': str(item_total_price),
                'total_additional_charges': str(total_additional_charges),
                'status': order.get_status_display(),
                'created_at': timezone.localtime(order.created_at).strftime('%d-%m-%Y %H:%M:%S'),
                'cancelled_at':timezone.localtime(order.cancelled_at).strftime('%d-%m-%Y %H:%M:%S') if order.cancelled_at else None,
                'customer_status': order.customer_status.capitalize(),
                'payment_method': order.payment.get_payment_method_display() if order.payment else '-',
                'payment_amount': str(order.payment.amount) if order.payment else '-',
                'transaction_id': order.payment.transaction_id if order.payment else '-',
                'payment_status': order.payment.get_status_display() if order.payment else '-',
                'payment_date': timezone.localtime(order.payment.payment_date).strftime('%d-%m-%Y %H:%M:%S') if order.payment and order.payment.payment_date else '-',
                'items': order_items,
                'additional_charges': additional_charges_data,
                'restaurant_name': order.restaurant.restaurant_name,
                'daily_sequence':order.daily_sequence,
            }
            print(order_data)
            return order_data
        except Order.DoesNotExist:
            return None"""