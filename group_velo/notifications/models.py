from django.contrib.auth import get_user_model
from django.db import models

from group_velo.data.choices import NotificationType
from group_velo.events.models import EventOccurence


# Create your models here.
class Notification(models.Model):
    user = models.ForeignKey(get_user_model(), null=False, blank=False, on_delete=models.CASCADE)
    notification_type = models.IntegerField("Notification Type", choices=NotificationType.choices)
    event_occurence = models.ForeignKey(EventOccurence, on_delete=models.CASCADE, blank=True, null=True)
    opened = models.BooleanField("Opened", default=False, null=False, blank=False)
    archived = models.BooleanField("Archived", default=False, null=False, blank=False)
    subject = models.TextField("Subject", null=False, blank=False)
    message = models.TextField("Message", null=True, blank=True)
    custom_message = models.TextField("Custom Message", null=True, blank=True)
    create_date = models.DateTimeField("Create Date", auto_now_add=True)

    def mark(self, read=True):
        self.opened = read
        self.save(update_fields=["opened"])
        return self

    def archive(self, archive=False):
        self.archived = archive
        self.save(update_fields=["archived"])
        return self

    def __str__(self):
        return f"{self.notification_type} {self.user.name} {self.create_date}"

    class Meta:
        indexes = [models.Index(fields=["user"])]
