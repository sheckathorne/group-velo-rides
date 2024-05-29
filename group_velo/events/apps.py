from django.apps import AppConfig
from django.db.models.signals import post_save, pre_save


class EventsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "group_velo.events"

    def ready(self):
        from group_velo.events.signals import post_event_occurence_save, remember_data

        from .models import EventOccurence

        pre_save.connect(remember_data, sender=EventOccurence)
        post_save.connect(post_event_occurence_save, sender=EventOccurence)
