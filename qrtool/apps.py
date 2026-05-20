from django.apps import AppConfig

class QrtoolConfig(AppConfig):
    # Django'nun varsayılan birincil anahtar alanı tipi.
    default_auto_field = "django.db.models.BigAutoField"
    # Uygulamanın proje içindeki kayıt adı.
    name = "qrtool"