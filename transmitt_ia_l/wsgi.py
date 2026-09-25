"""
WSGI config for condocdat project.
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'transmitt_ia_l.settings')
application = get_wsgi_application()
