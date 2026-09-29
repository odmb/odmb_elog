from django.apps import AppConfig


class ElogConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'elog'

    def ready(self):
        from . import signals  # noqa: F401
