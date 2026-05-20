from django.urls import path
from .views import index


# Uygulamanın tek giriş noktası ana sayfadır.
urlpatterns = [
    path("", index, name="index"),
]