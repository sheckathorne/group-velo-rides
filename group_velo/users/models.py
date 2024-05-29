import datetime
import os
import random
import urllib.parse
import uuid

import pytz
from django import forms
from django.apps import apps
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import CharField, Count, F, Q, Value
from django.template.defaultfilters import slugify
from django.urls import reverse

# from django.utils import timezone
from django_initials_avatar.templatetags.initials_avatar import render_initials_avatar
from phonenumber_field.modelfields import PhoneNumberField
from sqids.sqids import Sqids

from config.settings.base import SQIDS_ALPHABET, SQIDS_MIN_LEN
from group_velo.data.choices import EventMemberType, MemberType, PrivacyLevel, Relationship, RequestStatus

# from datetime import timedelta


def days_from_today(n):
    return datetime.date.today() + datetime.timedelta(days=n)


def length_of_five(value):
    if len(value) != 5:
        raise ValidationError("Zip code should have a length of five")


def numeric_chars(value):
    if not value.isnumeric():
        raise ValidationError(f"{value} should be numbers only")


class User(AbstractUser):
    """
    Default custom user model for Group Velo.
    If adding fields that need to be filled at user signup,
    check forms.SignupForm and forms.SocialSignupForms accordingly.
    """

    def image_upload_to(self, instance=None):
        if instance:
            ext = instance.split(".")[-1]
            filename = f"{uuid.uuid4()}.{ext}"
            return os.path.join("CustomUser", self.slug, filename)
        return None

    @property
    def get_avatar(self):
        if not self.avatar:
            return render_initials_avatar(f"{self.name}")
        return self.avatar.url

    # First and last name do not cover name patterns around the globe
    name = models.CharField("Full Name", max_length=255)
    # first_name = None  # type: ignore
    # last_name = None  # type: ignore
    email = models.EmailField(unique=True)
    address = models.CharField("Address", max_length=40, null=True, blank=True)
    zip_code = models.CharField("Zip Code", max_length=5, validators=[numeric_chars, length_of_five])
    avatar = models.ImageField(default=None, null=True, blank=True, upload_to=image_upload_to, max_length=255)
    about = models.TextField("About me", null=True, blank=True, max_length=3000)
    slug = models.SlugField(max_length=100)

    def get_absolute_url(self) -> str:
        """Get URL for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:detail", kwargs={"username": self.username})

    def __str__(self):
        return f"{self.email}"

    def available_ride_count(self, days_in_future):
        return self.available_rides(days_in_future).values("club").annotate(count=Count("club"))

    def registered_ride_count(self, days_in_future):
        return (
            self.upcoming_rides(days_in_future)
            .values("event_occurence__club")
            .annotate(count=Count("event_occurence__club"))
        )

    @property
    def random_avatar_color_pair(self):
        colors = [
            {"background": "#005f73", "text": "#FFFFFF"},
            {"background": "#0a9396", "text": "#000000"},
            {"background": "#94d2bd", "text": "#000000"},
            {"background": "#ee9b00", "text": "#000000"},
            {"background": "#ca6702", "text": "#000000"},
            {"background": "#bb3e03", "text": "#FFFFFF"},
            {"background": "#ae2012", "text": "#FFFFFF"},
            {"background": "#9b2226", "text": "#FFFFFF"},
        ]

        random.seed(self.id)
        choice = random.choice(colors)
        return choice

    def clubs_and_rides(self, clubs, days_in_future):
        available_ride_count = self.available_ride_count(days_in_future)
        registered_ride_count = self.registered_ride_count(days_in_future)
        verification_request = apps.get_model("clubs.ClubVerificationRequest")
        clubs_and_rides = []

        for membership in clubs:
            ride_count = (
                0
                if not available_ride_count.filter(club__id=membership.club.id)
                else available_ride_count.get(club__id=membership.club.id)["count"]
            )

            reg_ride_count = (
                0
                if not registered_ride_count.filter(event_occurence__club__id=membership.club.id)
                else registered_ride_count.get(event_occurence__club__id=membership.club.id)["count"]
            )

            club_verification_request_exists = verification_request.objects.filter(club=membership.club).exists()

            club_is_active = membership.club.active
            user_can_manage_club = membership.user_can_manage_club
            no_verification_request = not club_verification_request_exists

            show_registered_rides_btn = reg_ride_count > 0 and club_is_active
            show_join_rides_btn = ride_count > 0 and club_is_active
            show_create_ride_btn = membership.can_create_club_rides and club_is_active
            show_manage_members_btn = user_can_manage_club and club_is_active
            show_edit_club_btn = user_can_manage_club
            show_request_verification_btn = no_verification_request and user_can_manage_club

            clubs_and_rides.append(
                {
                    "membership": membership,
                    "available_ride_count": ride_count,
                    "registered_ride_count": reg_ride_count,
                    "show_registered_rides_btn": show_registered_rides_btn,
                    "show_join_rides_btn": show_join_rides_btn,
                    "show_create_ride_btn": show_create_ride_btn,
                    "show_manage_members_btn": show_manage_members_btn,
                    "show_edit_club_btn": show_edit_club_btn,
                    "show_request_verification_btn": show_request_verification_btn,
                }
            )

        return clubs_and_rides

    def upcoming_rides(self, days_in_future=366):
        event_occurence_member = apps.get_model("events.EventOccurenceMember")
        return event_occurence_member.objects.select_related(
            "event_occurence", "event_occurence__club", "event_occurence__route"
        ).filter(
            Q(
                user=self,
                event_occurence__ride_date__lte=days_from_today(days_in_future),
                event_occurence__ride_date__gte=datetime.date.today(),
            ),
            (
                Q(
                    event_occurence__club__active=True,
                    event_occurence__club__isnull=False,
                )
                | Q(event_occurence__club__isnull=True)
            ),
        )

    def waitlisted_rides(self, days_in_future=365):
        event_occurence_member = apps.get_model("events.EventOccurenceMemberWaitlist")
        return event_occurence_member.objects.select_related(
            "event_occurence", "event_occurence__club", "event_occurence__route"
        ).filter(
            Q(
                user=self,
                event_occurence__ride_date__lte=days_from_today(days_in_future),
                event_occurence__ride_date__gte=datetime.date.today(),
            ),
            (
                Q(
                    event_occurence__club__active=True,
                    event_occurence__club__isnull=False,
                )
                | Q(event_occurence__club__isnull=True)
            ),
        )

    # need to subtract the rides here that the user has joined in the waitlist
    def available_rides(self, days_in_future=366):
        event_occurence = apps.get_model("events.EventOccurence")
        event_occurence_member = apps.get_model("events.EventOccurenceMember")
        event_occurence_waitlist = apps.get_model("events.EventOccurenceMemberWaitlist")
        club_membership = apps.get_model("clubs.ClubMembership")

        return (
            event_occurence.objects.select_related("club", "route")
            .exclude(
                Q(pk__in=event_occurence_member.objects.filter(user=self).values("event_occurence"))
                | Q(pk__in=event_occurence_waitlist.objects.filter(user=self).values("event_occurence")),
            )
            .filter(
                privacy__lte=EventMemberType.Open,
                club__in=club_membership.objects.filter(
                    Q(user=self),
                    (Q(club__active=True, club__isnull=False) | Q(club__isnull=True)),
                ).values("club"),
            )
            .filter(
                ride_date__lte=days_from_today(days_in_future),
                ride_date__gte=datetime.date.today(),
            )
        )

    def clubs(self):
        club_membership = apps.get_model("clubs.ClubMembership")

        clubs = club_membership.objects.select_related("club").filter(
            Q(user=self, club__active=True, active=True)
            | Q(
                user=self,
                active=True,
                membership_type__lte=MemberType(MemberType.Admin).value,
                club__active=False,
            )
        )

        return clubs

    def routes(self):
        route = apps.get_model("routes.Route")
        return route.objects.select_related("created_by", "club").filter(
            Q(created_by=self) & (Q(club__active=True) | Q(club__isnull=True))
        )

    def route_clubs(self, membership_type):
        club = apps.get_model("clubs.Club")
        club_membership = apps.get_model("clubs.ClubMembership")
        route = apps.get_model("routes.Route")

        club.objects.filter(
            active=True,
            pk__in=route.objects.filter(
                shared=True,
            ).values("club"),
        )

        user_has_routes = route.objects.filter(created_by=self).exists()

        club_choices = club.objects.filter(
            active=True,
            pk__in=club_membership.objects.filter(user=self, membership_type__lte=membership_type.value).values(
                "club"
            ),
        )

        if not user_has_routes:
            club_choices = club_choices.filter(active=True, pk__in=route.objects.filter(shared=True).values("club"))

        return list(forms.ModelChoiceField(club_choices).choices)

    def route_create_clubs(self, membership_type):
        club = apps.get_model("clubs.Club")
        club_membership = apps.get_model("clubs.ClubMembership")

        return list(
            forms.ModelChoiceField(
                club.objects.filter(
                    active=True,
                    pk__in=club_membership.objects.filter(
                        user=self, membership_type__lte=membership_type.value
                    ).values("club"),
                )
            ).choices
        )

    def self_and_club_routes(self):
        route = apps.get_model("routes.Route")
        club_membership = apps.get_model("clubs.ClubMembership")

        return route.objects.select_related("created_by").filter(
            (Q(created_by=self) & (Q(club__active=True, club__isnull=False) | Q(club__isnull=True)))
            | (
                Q(
                    club__in=club_membership.objects.filter(
                        user=self,
                        club__active=True,
                        membership_type__lte=MemberType(MemberType.RideLeader).value,
                    ).values("club")
                )
                & Q(shared=True)
            )
        )

    def get_club_membership_request_status(self, club):
        club_membership_request = apps.get_model("clubs.ClubMembershipRequest")
        mem_request = club_membership_request.objects.filter(user=self, club=club).last()

        if mem_request.status == RequestStatus.Approved:
            return "joined"
        else:
            return "pending"

    def club_search_clubs(self, club_name):
        club_membership_request = apps.get_model("clubs.ClubMembershipRequest")
        club = apps.get_model("clubs.Club")

        pending_membership_requests = club_membership_request.objects.filter(
            user=self, status=RequestStatus(RequestStatus.Pending).value
        ).values("club")

        if club_name:
            all_clubs = club.objects.filter(name__icontains=club_name)
        else:
            all_clubs = club.objects.all()

        member_of_clubs = all_clubs.annotate(membership_status_text=Value("member", output_field=CharField())).filter(
            pk__in=self.clubs().values("club")
        )

        clubs_with_pending_requests = (
            all_clubs.annotate(membership_status_text=Value("pending", output_field=CharField()))
            .filter(pk__in=pending_membership_requests)
            .exclude(pk__in=member_of_clubs.values("id"))
        )

        joinable_clubs = (
            all_clubs.filter(privacy_level__lte=PrivacyLevel(PrivacyLevel.SemiPrivate).value)
            .annotate(membership_status_text=Value("joinable", output_field=CharField()))
            .exclude(pk__in=member_of_clubs.union(clubs_with_pending_requests).values("id"))
        )

        requestable_clubs = (
            all_clubs.filter(privacy_level__gte=PrivacyLevel(PrivacyLevel.Private).value)
            .annotate(membership_status_text=Value("requestable", output_field=CharField()))
            .exclude(pk__in=member_of_clubs.union(clubs_with_pending_requests).values("id"))
        )

        return member_of_clubs.union(clubs_with_pending_requests.union(joinable_clubs.union(requestable_clubs)))

    def create_club_membership_request(self, club):
        club_membership_request = apps.get_model("clubs.ClubMembershipRequest")
        club_membership = apps.get_model("clubs.ClubMembership")
        membership_exists = club_membership.objects.filter(user=self, club=club).exists()

        if membership_exists:
            return f"You already have a membership to {club.name}"
        else:
            if club.privacy_level == PrivacyLevel.Open:
                club_membership_request.objects.create(user=self, club=club, status=RequestStatus.Approved)
                # Create a forever paid membership
                self.create_club_membership(club, membership_type=MemberType.PaidMember)
                return f"Succesfully joined {club.name} as a paid member."
            elif club.privacy_level == PrivacyLevel.SemiPrivate:
                # ONE_YEAR_FROM_NOW = timezone.now() + timedelta(days=365)
                club_membership_request.objects.create(user=self, club=club, status=RequestStatus.Approved)
                # Create a forever unpaid membership
                self.create_club_membership(
                    club,
                    membership_type=MemberType.UnpaidMember,
                )
                return f"Succesfully joined {club.name} as an unpaid member."
            else:
                # Do not automatically create a membership
                club_membership_request.objects.create(user=self, club=club)

            return f"Request to join {club.name} submitted successfully"

    def create_club_membership(
        self,
        club,
        membership_type=MemberType.UnpaidMember,
        expiration_date_time=datetime.datetime(9999, 12, 31, 23, 59, 59, 0, pytz.UTC),
    ):
        club_membership = apps.get_model("clubs.ClubMembership")
        club_membership.objects.create(
            user=self,
            club=club,
            membership_type=membership_type,
            membership_expires=expiration_date_time,
        )

    def emergency_contacts(self):
        return EmergencyContact.objects.filter(contact_for=self)

    @property
    def has_emergency_contacts(self):
        return EmergencyContact.objects.filter(contact_for=self).exists()

    def club_membership_request_count(self):
        club_membership = apps.get_model("clubs.ClubMembership")
        club_membership_request = apps.get_model("clubs.ClubMembershipRequest")

        admin_of_clubs = club_membership.objects.filter(
            user=self, membership_type__lte=MemberType(MemberType.Admin).value
        ).values("club")

        club_membership_request_count = (
            club_membership_request.objects.filter(
                club__in=admin_of_clubs,
                status=RequestStatus(RequestStatus.Pending).value,
            )
            .values(pending_club_id=F("club__id"))
            .annotate(total=Count("pending_club_id"))
        )

        return club_membership_request_count

    def club_verification_request_count(self):
        club_verification_request_count = 0
        if self.is_superuser:
            club_verification_request = apps.get_model("clubs.ClubVerificationRequest")
            club_verification_request_count = club_verification_request.objects.filter(
                status=RequestStatus(RequestStatus.Pending).value,
            ).count()

        return club_verification_request_count

    def unread_notifications(self):
        notification = apps.get_model("notifications.Notification")
        return notification.objects.filter(user=self, opened=False, archived=False)

    def notifications(self):
        notification_date_range = days_from_today(-31)

        # notifications in the last 14 days
        all_notifications = apps.get_model("notifications.Notification").objects.filter(
            user=self, create_date__gte=notification_date_range, archived=False
        )

        unread_notifications = all_notifications.filter(opened=False).annotate(view_type=Value(1))
        stale_notifications = all_notifications.filter(opened=True).annotate(view_type=Value(2))

        return unread_notifications.union(stale_notifications).order_by("view_type", "-create_date")

    def archived_notifications(self):
        notification_date_range = days_from_today(-31)
        archived_notifications = apps.get_model("notifications.Notification").objects.filter(
            user=self, create_date__gte=notification_date_range, archived=True
        )

        unread_notifications = archived_notifications.filter(opened=False).annotate(view_type=Value(1))
        stale_notifications = archived_notifications.filter(opened=True).annotate(view_type=Value(2))

        return unread_notifications.union(stale_notifications).order_by("view_type", "-create_date")

    def saved_filters(self):
        return apps.get_model("users.SavedFilter").objects.filter(user=self).order_by("-create_date")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.slug:
            sqids = Sqids(alphabet=SQIDS_ALPHABET, min_length=SQIDS_MIN_LEN)
            self.slug = slugify(f"{self.name}") + f"-{sqids.encode([self.pk])}"
            self.save()


class EmergencyContact(models.Model):
    name = models.CharField("Name", max_length=100, blank=False)
    phone_number = PhoneNumberField(blank=False)
    relationship = models.IntegerField("Relationship", choices=Relationship.choices, blank=False)
    contact_for = models.ForeignKey(User, on_delete=models.CASCADE, related_name="emergencycontacts")


class SavedFilter(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField("Filter Name", max_length=50)
    filter_dict = models.JSONField(default=dict)
    create_date = models.DateTimeField("Create Date", auto_now_add=True)

    def filter_to_url(self):
        return urllib.parse.urlencode(self.filter, doseq=True)

    def __str__(self):
        return f"{self.user.name} - {self.name}"

    class Meta:
        unique_together = [["user", "name"], ["user", "filter_dict"]]
