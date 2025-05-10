import datetime

from django.apps import apps
from django.contrib.auth import get_user_model
from django.db import models
from localflavor.us.us_states import STATE_CHOICES as RAW_STATE_CHOICES

from group_velo.clubs.models import Club
from group_velo.data.validators import length_of_five, numeric_chars

STATE_CHOICES = tuple(RAW_STATE_CHOICES)


class RouteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related()


class Route(models.Model):
    name = models.CharField("Route Name", max_length=240)
    start_location_name = models.CharField("Start Location Name", max_length=240)
    start_address = models.CharField("Address", max_length=255, blank=True, null=True)
    start_city = models.CharField("City", max_length=40, null=True, blank=True)
    start_state = models.CharField("State", max_length=2, choices=STATE_CHOICES, null=True, blank=True)
    start_zip_code = models.CharField(
        "Zip Code",
        null=True,
        blank=True,
        max_length=5,
        validators=[numeric_chars, length_of_five],
    )
    url = models.CharField("Route URL", max_length=255)
    distance = models.DecimalField("Distance (miles)", max_digits=7, decimal_places=2)
    elevation = models.IntegerField("Elevation (ft)")
    created_by = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    shared = models.BooleanField("Share With Club", default=False)
    club = models.ForeignKey(Club, blank=True, null=True, on_delete=models.CASCADE)
    date_created = models.DateField("Date Created", auto_now_add=True)
    objects = RouteManager()

    @property
    def has_start_address(self):
        return self.start_address and ((self.start_city and self.start_state) or self.start_zip_code)

    def google_map_start_address(self):
        url = f"https://www.google.com/maps/place/{self.start_address.replace(' ','+')},"
        url = url + (
            f"+{self.start_city.replace(' ','+')},+{self.start_state}"
            if (self.start_city and self.start_state)
            else ""
        )
        url = url + f"+{self.start_zip_code}" if self.start_zip_code else ""
        return url

    def save(self, *args, **kwargs):
        created = self.pk is None
        super().save(*args, **kwargs)
        if created:
            UserRoute.objects.create(user=self.created_by, route=self)

    def num_rides(self):
        event_occurence = apps.get_model("events.EventOccurence")
        return event_occurence.objects.filter(
            is_canceled=False,
            ride_date__lt=datetime.date.today(),
            route=self,
        ).count()

    def __str__(self):
        return f"{self.name}, by {self.created_by.name} - {self.distance} miles"


class UserRoute(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    route = models.ForeignKey(Route, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.route.name} for profile {self.user} by {self.route.created_by}"
