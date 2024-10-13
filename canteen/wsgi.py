import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'canteen.settings')  # Ensure the correct project name

application = get_wsgi_application()
