import os
from django.core.wsgi import get_wsgi_application

# For production use the prod settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.prod')

application = get_wsgi_application()