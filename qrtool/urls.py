from django.urls import path
from .views import index


# ana index yöntemi için URL yapılandırması
urlpatterns = [
    path("", index, name="index"),
]