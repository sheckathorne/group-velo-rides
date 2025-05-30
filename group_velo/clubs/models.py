import datetime
import os
import uuid
from datetime import timedelta

import pytz
from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Count
from django.template.defaultfilters import slugify
from django.utils import timezone
from localflavor.us.us_states import STATE_CHOICES as RAW_STATE_CHOICES
from phonenumber_field.modelfields import PhoneNumberField

from group_velo.data.choices import GroupClassification, MemberType, PrivacyLevel, RequestStatus, SurfaceType
from group_velo.data.models import get_coords_of
from group_velo.data.validators import length_of_five, numeric_chars
from group_velo.events.fields import CharFieldAllowsMultiSelectSearch
from group_velo.utils.mixins import SqidMixin

STATE_CHOICES = tuple(RAW_STATE_CHOICES)


class Club(models.Model, SqidMixin):
    def image_upload_to(self, instance=None):
        if instance:
            ext = instance.split(".")[-1]
            filename = f"{uuid.uuid4()}.{ext}"
            return os.path.join("Club", self.slug, filename)
        return ""

    @property
    def get_logo(self):
        if not self.logo:
            return "/media/default/bicycle.png"
        return self.logo.url

    name = models.CharField("Club Name", max_length=255)
    abbreviation = models.CharField("Club Abbreviation", max_length=5, blank=True, null=True)
    url = models.CharField("Website", max_length=255)
    logo = models.ImageField(
        default="default/bicycle.png",
        null=True,
        blank=True,
        upload_to=image_upload_to,
        max_length=255,
    )
    city = models.CharField("City", max_length=50, null=False, blank=False)
    state = models.CharField(max_length=2, choices=STATE_CHOICES, null=False, blank=False)
    zip_code = models.CharField("Zip Code", max_length=5, validators=[numeric_chars, length_of_five])
    email_address = models.EmailField("Email", max_length=255, blank=True, null=True)
    phone_number = PhoneNumberField("Phone Number", blank=True, null=True)
    latitude = models.DecimalField("Latitude", max_digits=9, decimal_places=6, null=False, blank=False)
    longitude = models.DecimalField("Latitude", max_digits=9, decimal_places=6, null=False, blank=False)
    private = models.BooleanField("Private", default=True, blank=False, null=False)
    privacy_level = models.IntegerField(
        "Privacy Level",
        choices=PrivacyLevel.choices,
        null=False,
        blank=False,
        default=PrivacyLevel(PrivacyLevel.Private).value,
    )
    create_date = models.DateField("Date Created", auto_now_add=True)
    founded_date = models.DateField("Date Founded", auto_now_add=True, null=False, blank=False)
    created_by = models.ForeignKey(get_user_model(), related_name="created_by_user", on_delete=models.CASCADE)
    edited_by = models.ForeignKey(
        get_user_model(),
        related_name="edited_by_user",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
    )
    edited_date = models.DateField("Date Edited", null=True, blank=True)
    slug = models.SlugField(max_length=100)
    description = models.TextField("Club description", max_length=3000)
    active = models.BooleanField("Active", default=True, blank=False, null=False)
    private_ride_attendence = models.BooleanField("Ride Attendence is Private", default=False, blank=False, null=False)
    private_ride_waitlist = models.BooleanField("Ride Waitlist is Private", default=False, blank=False, null=False)
    allow_ride_discussion = models.BooleanField("Allow Ride Discussion", default=True, blank=False, null=False)
    strict_ride_classification = models.BooleanField(
        "Strict Ride Classification", default=False, blank=False, null=False
    )
    verified = models.BooleanField("Verified", default=False, blank=False, null=False)

    @property
    def member_count(self):
        return ClubMembership.objects.filter(club=self).count()

    def save(self, *args, **kwargs):
        if length_of_five(self.zip_code) != ValidationError and numeric_chars(self.zip_code) != ValidationError:
            self.latitude, self.longitude = get_coords_of(self.zip_code)

        created = self.pk is None
        self.slug = slugify(f"{self.name}") + f"-{self.encode_sqid(self.pk)}"

        super().save(*args, **kwargs)

        if created:
            timezone = pytz.utc
            membership_expires = timezone.localize(
                datetime.datetime(year=9999, month=12, day=31, hour=23, minute=59, second=59)
            )
            ClubMembership.objects.create(
                user=self.created_by,
                club=self,
                active=True,
                membership_expires=membership_expires,
                membership_type=MemberType.Creator,
            )

    def __str__(self):
        return self.name

    def active_members(self):
        return ClubMembership.objects.filter(club=self, club__active=True)

    def active_memberships(self):
        return ClubMembership.objects.filter(club=self, club__active=True, active=True)

    def membership_requests(self):
        return ClubMembershipRequest.objects.filter(club=self, club__active=True)

    def pending_requests(self):
        return self.membership_requests().filter(status=RequestStatus.Pending)

    @property
    def active_and_current_member_count(self):
        now = timezone.now()

        return (
            ClubMembership.objects.select_related("club")
            .filter(club=self, membership_expires__gte=now, active=True)
            .count()
        )

    @property
    def club_admins(self):
        now = timezone.now()
        return ClubMembership.objects.select_related("club", "user").filter(
            club=self,
            membership_expires__gte=now,
            active=True,
            membership_type__lte=MemberType(MemberType.Admin).value,
        )

    @property
    def total_rides(self):
        now = timezone.now()
        one_year_ago = timezone.now() - timedelta(days=365)
        event_occurence_member = apps.get_model("events.EventOccurenceMember")
        return (
            event_occurence_member.objects.select_related("user", "event_occurence", "club")
            .filter(
                event_occurence__club=self,
                event_occurence__ride_date__lt=now,
                event_occurence__ride_date__gt=one_year_ago,
                attended=True,
            )
            .values("user")
            .annotate(ride_count=Count("id"))
            .order_by("-ride_count")
        )


class ClubMembership(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    club = models.ForeignKey(Club, on_delete=models.CASCADE)
    create_date = models.DateField("Date Joined", auto_now_add=True)
    membership_expires = models.DateTimeField("Membership Expires")
    active = models.BooleanField("Active", default=True)
    membership_type = models.IntegerField("Membership Type", choices=MemberType.choices)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "club"], name="One user membership per club")]

    def is_expired(self):
        return self.membership_expires < timezone.now()

    def is_inactive(self):
        return not self.active

    @property
    def level(self):
        return MemberType(self.membership_type).label

    @property
    def can_create_club_rides(self):
        return MemberType(self.membership_type).value <= MemberType(MemberType.RideLeader).value

    @property
    def expired(self):
        return self.is_expired()

    @property
    def inactive(self):
        return not self.active

    @property
    def user_can_manage_club(self):
        return self.membership_type <= MemberType(MemberType.Admin).value

    @property
    def membership_type_label(self):
        return MemberType(self.membership_type).label

    def __str__(self):
        return self.club.name + " - " + self.user.name + " - " + MemberType(self.membership_type).label


class ClubMembershipRequest(models.Model):
    club = models.ForeignKey(Club, on_delete=models.CASCADE)
    user = models.ForeignKey(get_user_model(), related_name="request_user", on_delete=models.CASCADE)
    responder = models.ForeignKey(
        get_user_model(),
        related_name="response_user",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )
    request_date = models.DateTimeField("Request Date", auto_now_add=True)
    response_date = models.DateTimeField("Response Date", blank=True, null=True)
    status = models.IntegerField("Request Status", choices=RequestStatus.choices, default=RequestStatus.Pending)

    @property
    def status_label(self):
        return RequestStatus(self.status).label

    def __str__(self):
        return f"{self.user.name} to join {self.club.name}"


class ClubRideClassificationLimit(models.Model):
    club = models.ForeignKey(Club, on_delete=models.CASCADE)
    surface_type = models.TextField(
        "Surface Type",
        choices=SurfaceType.choices,
        blank=False,
        null=False,
        max_length=1,
    )
    group_classification = CharFieldAllowsMultiSelectSearch(
        "Ride Classification", choices=GroupClassification.choices, max_length=2
    )
    lower_pace_range = models.DecimalField("Lower Pace Range", max_digits=3, decimal_places=1)
    upper_pace_range = models.DecimalField("Upper Pace Range", max_digits=3, decimal_places=1)
    active = models.BooleanField("Active", default=True, blank=False, null=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["club", "surface_type", "group_classification"],
                name="There can only be one pace range per club, surface, and classification",
            )
        ]


class ClubVerificationRequest(models.Model):
    club = models.ForeignKey(Club, on_delete=models.CASCADE)
    created_by = models.ForeignKey(
        get_user_model(),
        related_name="verification_request_user",
        on_delete=models.CASCADE,
    )
    contact_email = models.EmailField(
        blank=False,
        max_length=255,
        null=False,
        verbose_name="Contact Email",
        help_text="You will be contacted for additional verification steps",
    )
    responder = models.ForeignKey(
        get_user_model(),
        related_name="verification_response_user",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )
    request_date = models.DateTimeField("Request Date", auto_now_add=True)
    response_date = models.DateTimeField("Response Date", blank=True, null=True)
    status = models.IntegerField("Request Status", choices=RequestStatus.choices, default=RequestStatus.Pending)

    @property
    def status_label(self):
        return RequestStatus(self.status).label

    def __str__(self):
        return f"{self.created_by.name} to verify {self.club.name}"
