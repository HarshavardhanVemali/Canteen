import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application
import canteenapp.routing  # Import after django.setup() to ensure apps are ready

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'canteen.settings')

# Set up Django
django.setup()

# Define the ASGI application
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                canteenapp.routing.websocket_urlpatterns
            )
        )
    ),
})
