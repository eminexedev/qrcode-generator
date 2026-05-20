import os
from django.core.wsgi import get_wsgi_application


# WSGI çalışma ortamı için Django ayar modülünü tanımlar.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "qrcode_project.settings")
# WSGI sunucularının (gunicorn/uwsgi vb.) kullanacağı uygulama nesnesi.
application = get_wsgi_application()