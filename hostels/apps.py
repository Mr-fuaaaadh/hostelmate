from django.apps import AppConfig

class HostelsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'hostels'

    def ready(self):
        import hostels.signals
