from django.contrib import admin
from django.urls import include, path


# Proje seviyesindeki URL yönlendirmeleri.
urlpatterns = [
    path("admin/", admin.site.urls),
    # Ana sayfa ve uygulama rotaları qrtool uygulamasından gelir.
    path("", include("qrtool.urls")),
]