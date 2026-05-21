import os
from django.core.asgi import get_asgi_application

# ASGI çalışma ortamı için Django ayar modülünü tanımlar.
# ASGI sunucuları (uvicorn/daphne vb.) bu ortam değişkenini kullanarak Django'nun hangi ayar dosyasını yükleyeceğini bilir.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "qrcode_project.settings")
# ASGI sunucularının (uvicorn/daphne vb.) kullanacağı uygulama nesnesi.
application = get_asgi_application()