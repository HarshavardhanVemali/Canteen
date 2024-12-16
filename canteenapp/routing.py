from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/menu/$', consumers.MenuConsumer.as_asgi()),
    re_path(r'ws/allitems/$', consumers.AllItemsConsumer.as_asgi()),
    re_path(r'ws/cartitems/$',consumers.CartItemConsumer.as_asgi()),
    re_path(r'ws/additionalprices/$',consumers.AdditionalPricesConsumer.as_asgi()),
    re_path(r'ws/searchupdate/$',consumers.SearchItemsConsumer.as_asgi()),
    re_path(r'ws/adminorderconsumer/$',consumers.AdminOrderConsumer.as_asgi()),
    re_path(r'ws/restaurantconsumers/$',consumers.RestaurantOrderConsumer.as_asgi()),
    re_path(r'ws/deliveryconsumers/$',consumers.DeliveryOrderConsumer.as_asgi()),
]