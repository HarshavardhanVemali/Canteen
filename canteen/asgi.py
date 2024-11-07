import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
from django.urls import path, re_path
from django.urls import include
import  canteenapp.routing
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'canteen.settings')
django.setup()

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                canteenapp.routing.websocket_urlpatterns
            )
        )
    ),
})
from django.conf import settings