import datetime
from datetime import timedelta
from decimal import Decimal

import pytz
from dateutil.relativedelta import relativedelta
from django.apps import apps
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import models
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.template.defaultfilters import slugify
from django.template.loader import render_to_string

from group_velo.clubs.models import Club, ClubMembership
from group_velo.data.choices import (
    DropDesignation,
    EmailType,
    EventMemberType,
    GroupClassification,
    MemberListType,
    NotificationType,
    RecurrenceFrequency,
    RoleType,
    SurfaceType,
)
from group_velo.routes.models import Route

from .fields import CharFieldAllowsMultiSelectSearch, ChoiceArrayField, DaysOfWeek


def daterange(start_date, end_date):
    # +1 on next line to be date inclusive
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)


def one_year_from(start_date, end_date):
    if end_date > start_date + relativedelta(days=+366):
        raise ValidationError("End date must be within 1 year of start date")


def upper_greater_than_lower_pace(lower, upper):
    if lower > upper:
        raise ValidationError("Upper pace range should be greater than lower " "pace range")


def ride_is_full(event_occurence):
    if event_occurence.ride_is_full():
        raise ValidationError(
            "Ride is full. You have been added to a waitlist for the ride and will "
            "be notified if and when your registration is completed."
        )


def max_is_fewer_than_riders(max_riders, number_of_riders):
    if max_riders and number_of_riders and max_riders < number_of_riders:
        raise ValidationError("Cannot set max riders fewer than number of signed " "up riders")


def membership_is_expired(expiration_date, event_date):
    if event_date > expiration_date:
        raise ValidationError("Club membership expires before event date")


def not_member_of_club(membership_exists):
    if not membership_exists:
        raise ValidationError("Must be a club member to join this event")


def create_occurence_from_event(event, event_date):
    EventOccurence.objects.create(
        event=event,
        occurence_name=event.name,
        slug=slugify(event.name),
        created_by=event.created_by,
        privacy=event.privacy,
        club=event.club,
        ride_date=event_date,
        ride_time=event.ride_time,
        time_zone=event.time_zone,
        max_riders=event.max_riders,
        is_canceled=event.is_canceled,
        route=event.route,
        start_zip_code=event.route.start_zip_code,
        surface_type=event.surface_type,
        drop_designation=event.drop_designation,
        group_classification=event.group_classification,
        lower_pace_range=event.lower_pace_range,
        upper_pace_range=event.upper_pace_range,
        description=event.description,
    )


def create_occurences_by_frequency(event, event_freq):
    selected_weekdays = [int(x) for x in event.weekdays]
    for event_date in daterange(event.start_date, event.end_date):
        if event_freq is RecurrenceFrequency.Daily:
            create_occurence_from_event(event, event_date)
        elif event_freq is RecurrenceFrequency.Weekly and event_date.weekday() in selected_weekdays:
            create_occurence_from_event(event, event_date)


class EventBase(models.Model):
    TIMEZONE_CHOICES = zip(pytz.all_timezones, pytz.all_timezones)

    created_by = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="%(class)s_created_by")
    privacy = models.IntegerField("Privacy", choices=EventMemberType.choices)
    club = models.ForeignKey(
        Club,
        null=True,
        blank=True,
        help_text="Only required if private is selected",
        on_delete=models.CASCADE,
    )
    ride_time = models.TimeField("Ride Time")
    time_zone = models.CharField(
        "Time Zone",
        default="America/Chicago",
        choices=TIMEZONE_CHOICES,
        max_length=100,
    )
    surface_type = models.TextField(
        "Surface Type",
        choices=SurfaceType.choices,
        blank=False,
        null=False,
        max_length=1,
    )
    drop_designation = models.IntegerField("Drop/No-drop", choices=DropDesignation.choices, blank=False, null=False)
    max_riders = models.PositiveIntegerField("Max Riders")
    is_canceled = models.BooleanField("Canceled", default=False)
    route = models.ForeignKey(Route, on_delete=models.CASCADE)

    lower_pace_range = models.DecimalField("Lower Pace Range", max_digits=3, decimal_places=1)
    upper_pace_range = models.DecimalField("Upper Pace Range", max_digits=3, decimal_places=1)
    group_classification = CharFieldAllowsMultiSelectSearch(
        "Classification", choices=GroupClassification.choices, max_length=2
    )
    description = models.TextField("Description", blank=True, null=True, max_length=2048)

    def create_notification(
        self,
        member,
        notification_type,
        subject,
        body,
        custom_message,
        event_occurence=None,
    ):
        notification = apps.get_model("notifications.Notification")

        new_notification = notification(
            user=member,
            notification_type=notification_type,
            event_occurence=event_occurence,
            subject=subject,
            message=body,
            custom_message=custom_message,
        )

        new_notification.save()

    def registered_users(self, exclude_id=None, user_ids=None):
        if not user_ids:
            user_ids = self.registered_user_ids()
        return get_user_model().objects.filter(pk__in=user_ids).exclude(pk=exclude_id)

    def send_event_email(self, member, template, subject, body, custom_message=None):
        message = render_to_string(
            template,
            {
                "body": body,
                "member": member,
                "custom_message": custom_message,
            },
        )

        if template and send_mail(
            subject,
            "plaintext email",
            "groupvelo@gmail.com",
            [member.email],
            html_message=message,
        ):
            return (True, member)
        else:
            return (False, member)

    def occurences_with_rider_count(self):
        return EventOccurence.objects.filter(event=self).annotate(rider_count=Count("eventoccurencemember_members"))

    class Meta:
        abstract = True


class Event(EventBase):
    name = models.CharField("Event Name", max_length=100)
    start_date = models.DateField("Start Date")
    end_date = models.DateField("End Date")
    frequency = models.IntegerField("Recurrence", choices=RecurrenceFrequency.choices)
    weekdays = ChoiceArrayField(
        models.IntegerField("Weekdays", choices=DaysOfWeek.choices),
        default=list,
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.name

    def registered_user_ids(self):
        return (
            EventOccurenceMember.objects.select_related("user")
            .filter(event_occurence__event__id=self.id)
            .values_list("user", flat=True)
            .distinct()
        )

    def is_created_by(self, user):
        return self.created_by == user

    def all_occurences(self, user_id):
        return EventOccurenceMember.objects.filter(event_occurence__event=self, user__id=user_id)

    @staticmethod
    def occurence_name_list(event_occurences):
        result = ""
        for event_occurence_member in event_occurences:
            result += (
                f"<li>{event_occurence_member.event_occurence.occurence_name.capitalize()} "
                f"on {event_occurence_member.event_occurence.ride_date.strftime('%-m/%-d/%Y')}</li>"
            )
        return result

    def generate_email_data(self, deleted_by, all_occurences):
        subject = f"CANCELED - {self.name} (Series)"
        message = (
            f"An event series containing the following rides was canceled. Your registration for the following "
            f"rides was canceled as a result:<ul>{self.occurence_name_list(all_occurences)}</ul>"
        )
        return subject, message

    def notify_member_list(self, request, deleted_by):
        notification_results = []
        notification_type = NotificationType.RideCancel
        members = self.registered_users(exclude_id=deleted_by.id)
        template = "events/emails/cancel_event_email.html"
        custom_message = request.POST.get("cancel-comment")
        for member in members:
            all_occurences = self.all_occurences(member.id)
            subject, body = self.generate_email_data(deleted_by, all_occurences)
            success, member = self.send_event_email(member, template, subject, body)
            super().create_notification(member, notification_type, subject, body, custom_message)
            notification_results.append((success, member))

        success = [i for i, j in notification_results]

        if all(success):
            messages.success(
                request,
                f"Successfully deleted {self.name}. All riders have been notified",
                extra_tags="timeout-5000",
            )
        elif not all(success):
            for result, member in list(filter(lambda x: not x[0], notification_results)):
                user = member.user
                messages.error(
                    request,
                    f"Failed to send cancelation email to {user.name} at {user.email}",
                )

            messages.success(
                request,
                f"Successfully deleted {self.name}. Not all riders were successfully notified",
            )
        else:
            messages.error(request, "Something went wrong and the event was not deleted.")

    def delete(self, *args, request=None, deleted_by=None, **kwargs):
        if deleted_by and request:
            self.notify_member_list(request, deleted_by)
        return super().delete()

    def clean(self):
        one_year_from(self.start_date, self.end_date)
        upper_greater_than_lower_pace(self.lower_pace_range, self.upper_pace_range)

    def save(self, *args, **kwargs):
        created = self.pk is None
        self.full_clean()
        super().save(*args, **kwargs)
        if created:
            event_freq = RecurrenceFrequency(self.frequency)
            if event_freq is RecurrenceFrequency.Zero:
                event_date = self.start_date + datetime.timedelta(days=0)
                create_occurence_from_event(self, event_date)
            else:
                create_occurences_by_frequency(self, event_freq)


class EventOccurence(EventBase):
    MINS_IN_HOUR = Decimal(60.0)

    class MaxRidersField(models.PositiveIntegerField):
        default_validators = []

    event = models.ForeignKey(Event, null=True, blank=True, on_delete=models.CASCADE)
    occurence_name = models.CharField("Event Name", max_length=100)
    slug = models.SlugField(max_length=255, blank=True)
    ride_date = models.DateField("Ride Date")
    start_zip_code = models.CharField(max_length=10)
    modified_by = models.ForeignKey(
        get_user_model(),
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        related_name="modified_by",
    )
    modified_date = models.DateTimeField("Modified Date", blank=True, null=True, auto_now=True)

    def estimated_ride_duration_mins(self):
        MINS_IN_QUARTER_HOUR = Decimal(15.0)
        ESTIMATED_STOP_PERCENTAGE = Decimal(0.10)
        distance = self.route.distance
        average_pace = (self.lower_pace_range + self.upper_pace_range) / 2
        estimated_duration = distance / average_pace
        total_minutes = estimated_duration * self.MINS_IN_HOUR * (1 + ESTIMATED_STOP_PERCENTAGE)
        rounded_minutes = round(total_minutes / MINS_IN_QUARTER_HOUR) * MINS_IN_QUARTER_HOUR
        return rounded_minutes

    def ride_rounded_start_and_end_hour(self):
        estimated_duration_mins = self.estimated_ride_duration_mins()
        ride_start_time = self.ride_time
        estimated_ride_end_time = ride_start_time + timedelta(minutes=estimated_duration_mins)

        # Round down to the start of the hour
        starting_hour = ride_start_time.replace(minute=0, second=0, microsecond=0)
        ending_hour = estimated_ride_end_time.replace(minute=0, second=0, microsecond=0)

        return starting_hour, ending_hour

    @property
    def estimated_ride_duration(self):
        rounded_minutes = self.estimated_ride_duration_mins()
        hours = int(rounded_minutes // self.MINS_IN_HOUR)
        minutes = int(rounded_minutes % self.MINS_IN_HOUR)
        parts = []
        if hours:
            parts.append(f"{hours} hr" + ("s" if hours != 1 else ""))

        if minutes:
            parts.append(f"{minutes} min" + ("s" if minutes != 1 else ""))

        return " ".join(parts)

    def waitlist_members(self):
        return (
            EventOccurenceMemberWaitlist.objects.select_related("user")
            .filter(event_occurence=self)
            .order_by("waitlist_join_date")
        )

    def members(self):
        return EventOccurenceMember.objects.select_related("user").filter(event_occurence=self).order_by("role")

    def registered_user_ids(self):
        return (
            EventOccurenceMember.objects.select_related("user")
            .filter(event_occurence__id=self.id)
            .values_list("user", flat=True)
            .distinct()
        )

    @property
    def return_group_classification_color(self):
        match GroupClassification(self.group_classification).value:
            case "A":
                return "bg-red-500 dark:bg-red-600"
            case "B":
                return "bg-orange-500 dark:bg-orange-600"
            case "C":
                return "bg-yellow-500 dark:bg-yellow-600"
            case "D":
                return "bg-green-500 dark:bg-green-600"
            case "N":
                return "bg-blue-500 dark:bg-blue-600"
            case "NA":
                return "bg-gray-500 dark:bg-gray-600"
            case _:
                return "bg-gray-500 dark:bg-gray-600"

    @property
    def ride_leader_users(self):
        leaders = (
            EventOccurenceMember.objects.select_related("user")
            .filter(
                event_occurence=self,
                role__lte=RoleType(RoleType.Leader).value,
            )
            .order_by("role")
        )

        return list(leaders)

    def ride_leaders(self):
        return EventOccurenceMember.objects.select_related("user").filter(
            event_occurence=self,
            role__lte=RoleType(RoleType.Leader).value,
        )

    def user_is_ride_leader(self, user):
        return self.ride_leaders().filter(user=user).exists()

    @property
    def time_until_ride(self):
        tz = pytz.timezone(self.time_zone)

        ride_datetime = datetime.datetime.combine(self.ride_date, self.ride_time)
        aware_ride_datetime = tz.localize(ride_datetime)
        current_datetime = datetime.datetime.now(tz)
        rd = relativedelta(aware_ride_datetime, current_datetime)

        time_diff = (
            f"{abs(rd.days)} day{'s'[:abs(rd.days) ^ 1]} and {abs(rd.hours)} hour{'s'[:abs(rd.hours) ^ 1]}"
            if abs(rd.days) > 0
            else f"{abs(rd.hours)} hour{'s'[:abs(rd.hours) ^ 1]}"
        )

        if rd.days + rd.hours == 0:
            return "Now"
        elif rd.days + rd.hours > 0:
            return f"({time_diff} from now)"
        else:
            return f"({time_diff} ago)"

    @property
    def is_private(self):
        return self.privacy == EventMemberType.Members

    @property
    def ride_leader_name(self):
        ride_leader_users = self.ride_leader_users

        return [
            {
                "name": f"{x.user.name}",
                "id": x.user.id,
                "slug": x.user.slug,
            }
            for x in ride_leader_users
        ]

    def can_be_joined_by(self, user):
        return (
            EventOccurence.objects.filter(
                Q(
                    Q(privacy=EventMemberType.Members),
                    Q(
                        club__in=ClubMembership.objects.filter(
                            user=user,
                            membership_type__lte=EventMemberType(EventMemberType.Members).value,
                            membership_expires__gte=self.ride_date,
                            active=True,
                            club__active=True,
                        ).values("club")
                    ),
                )
                | Q(
                    Q(privacy=EventMemberType.Open),
                    Q(
                        club__in=ClubMembership.objects.filter(
                            user=user,
                            membership_type__lte=EventMemberType(EventMemberType.Open).value,
                            club__active=True,
                        ).values("club")
                    ),
                )
            )
            .filter(pk=self.pk)
            .exists()
        )

    @property
    def number_of_riders(self):
        return EventOccurenceMember.objects.filter(event_occurence__id=self.id).count()

    def registered_rider_count(self):
        return EventOccurenceMember.objects.filter(event_occurence__id=self.id).count()

    def waitlist_rider_count(self):
        return EventOccurenceMemberWaitlist.objects.filter(event_occurence__id=self.id).count()

    @property
    def percentage_full(self):
        return (self.number_of_riders / float(self.max_riders)) * 100

    @property
    def nearly_full(self):
        open_slots = self.max_riders - self.number_of_riders
        nearly_full = (
            (self.max_riders >= 30 and self.percentage_full >= 90)
            or (30 > self.max_riders >= 15 and self.percentage_full >= 80)
            or (self.max_riders < 15 and self.percentage_full >= 70)
            or (open_slots <= 2)
        )
        return nearly_full

    @property
    def progress_bar_class(self):
        if self.max_riders == self.number_of_riders:
            return "progress-bar bg-danger"
        elif self.nearly_full:
            return "progress-bar bg-warning"
        else:
            return "progress-bar bg-success"

    @property
    def group_classification_name(self):
        return GroupClassification(self.group_classification).label

    @property
    def group_classification_abbreviation(self):
        return GroupClassification(self.group_classification).value

    def comments(self):
        return EventOccurenceMessage.objects.filter(
            (Q(event_occurence__club__active=True) | Q(event_occurence__club__isnull=True)),
            event_occurence=self,
        )

    def ride_is_full(self):
        return self.number_of_riders >= self.max_riders

    def registered_riders(self):
        return EventOccurenceMember.objects.select_related("user").filter(event_occurence=self).only("user")

    def generate_email_data(self, user, email_type, original_ride_date):
        if email_type == EmailType.CANCEL:
            subject = f"{self.occurence_name.capitalize()} Canceled for {self.ride_date.strftime('%-m/%-d/%Y')}"
            body = f"{self.occurence_name.capitalize()} on {self.ride_date.strftime('%-m/%-d/%Y')} has been "
            f"canceled by {user.name}"
            template = "events/emails/cancel_event_occurence_email.html"
        else:
            subject = f"{self.occurence_name.capitalize()} on {original_ride_date.strftime('%-m/%-d/%Y')} "
            "was modified"
            body = f"{self.occurence_name.capitalize()} on {original_ride_date.strftime('%-m/%-d/%Y')} "
            "has been modified by {user.name}"
            template = "events/emails/modify_event_occurence_email.html"

        return subject, body, template

    def notify_member_list(
        self,
        submitted_by,
        email_type,
        request=None,
        custom_message=None,
        original_ride_date=None,
    ):
        class RequestMessage:
            verbs = {
                EmailType.CANCEL: ("deleted", "cancelation"),
                EmailType.MODIFY: ("modified", "modification"),
            }

            def __init__(self, event_occurence, email_type):
                self.success = f"Successfully {self.verbs[email_type][0]} {event_occurence.occurence_name}. "
                "all riders have been notified"
                self.partial = f"Successfully {self.verbs[email_type][0]} {event_occurence.occurence_name}. "
                "Not all riders were successfully notified"
                self.other = f"Something went wrong and the event was not {self.verbs[email_type][0]}."

            def compose_failure(self, user):
                self.failure = f"Failed to send {self.verbs[email_type][1]} email to "
                f"{user.name} at {user.email}"

        notification_results = []
        notification_type = (
            NotificationType.RideCancel if email_type == EmailType.CANCEL else NotificationType.RideChange
        )
        members = self.registered_users(exclude_id=submitted_by.id)
        subject, body, template = self.generate_email_data(submitted_by, email_type, original_ride_date)
        request_message = RequestMessage(self, email_type)
        for member in members:
            success, member = self.send_event_email(member, template, subject, body, custom_message)
            super().create_notification(member, notification_type, subject, body, custom_message)
            notification_results.append((success, member))

        if email_type == EmailType.CANCEL:
            self.create_banner_message(request, request_message, notification_results)

    def create_banner_message(self, request, request_message, notification_results):
        success = [i for i, j in notification_results]

        if all(success):
            messages.success(
                request,
                request_message.success,
                extra_tags="timeout-5000",
            )
        elif not all(success):
            for result, member in list(filter(lambda x: not x[0], notification_results)):
                request_message.compose_failure(member.user)
                messages.error(
                    request,
                    request_message.failure,
                )

            messages.success(
                request,
                request_message.partial,
            )
        else:
            messages.error(request, request_message.failure)

    def promote_from_waitlist_to_ride(self):
        def there_are_riders_to_promote_to_available_space():
            return self.waitlist_rider_count() > 0 and self.max_riders - self.registered_rider_count() > 0

        while there_are_riders_to_promote_to_available_space():
            wailist_member = (
                EventOccurenceMemberWaitlist.objects.filter(event_occurence=self)
                .order_by("waitlist_join_date")
                .first()
            )

            member_to_promote = wailist_member.user

            data = {
                "user": member_to_promote,
                "event_occurence": self,
                "role": RoleType(RoleType.Rider).value,
            }

            event_occurence_member = EventOccurenceMember(**data)

            try:
                event_occurence_member.save()
            finally:
                self.remove_rider_from_waitlist(member_to_promote)
                self.notify_rider_of_promotion(member_to_promote)

    def remove_rider_from_waitlist(self, member_to_promote):
        waitlist_member = get_object_or_404(
            EventOccurenceMemberWaitlist,
            user=member_to_promote,
            event_occurence=self,
        )

        waitlist_member.delete()

        waitlist_member = EventOccurenceMemberWaitlist.objects.filter(user=member_to_promote, event_occurence=self)

    def notify_rider_of_promotion(self, member_to_promote):
        mail_subject = f"Registered to {self.occurence_name} from waitlist"
        message = render_to_string(
            "events/emails/promoted_to_ride_from_waitlist_email.html",
            {
                "event_occurence": self,
                "member": member_to_promote,
            },
        )

        to_email = member_to_promote.email
        send_mail(
            mail_subject,
            "plaintext email",
            "groupvelo@gmail.com",
            [to_email],
            html_message=message,
        )

        notification_type = NotificationType.WaitlistPromotion
        subject = f"Promoted from waitlist for {self.occurence_name}"
        message = (
            f"You have been added to the main ride registration list for {self.occurence_name} "
            f"happening on {self.ride_date.strftime('%A, %B %-d')}."
            "If you are unable to join the ride, please cancel your registration. Otherwise, show up and ride!"
        )
        custom_message = None
        super().create_notification(member_to_promote, notification_type, subject, message, custom_message)

    @staticmethod
    def assign_user_colors(event_comments):
        colors = [
            ("text-red-800 dark:text-red-500", "#991b1b"),
            ("text-green-500 dark:text-green-300", "#22c55e"),
            ("text-orange-500 dark:text-orange-400", "#f97316"),
            ("text-cyan-500 dark:text-cyann-300", "#06b6d4"),
            ("text-fuchsia-500 dark:text-fuchsia-300", "#d946ef"),
            ("text-indigo-500 dark:text-indigo-300", "#6366f1"),
            ("text-rose-500 dark:text-rose-300", "#f43f5e"),
            ("text-coolgray-700 dark:text-coolgray-400", "#374151"),
        ]

        distinct_users = event_comments.values("user").distinct()

        for i, user in enumerate(distinct_users):
            user["color"] = colors[i % len(colors)]

        final_data = []
        for comment in event_comments:
            color = next(
                (u for u in distinct_users if u["user"] == comment.user.id),
                {"color": ("text-black", "#000000")},
            )["color"]
            final_data.append({"comment": comment, "color": color})

        return final_data

    def sorted_and_colored_comments(self, sort_asc=False):
        comments = self.comments()
        comments_with_colors = self.assign_user_colors(comments)
        return sorted(
            comments_with_colors,
            key=lambda c: c["comment"].create_date,
            reverse=sort_asc,
        )

    def delete(self, *args, request=None, deleted_by=None, explicit_delete=False, **kwargs):
        if explicit_delete:
            email_type = EmailType.CANCEL
            self.notify_member_list(deleted_by, email_type, request=request)
        return super().delete()

    def clean(self):
        max_is_fewer_than_riders(self.max_riders, self.number_of_riders)

    def save(self, *args, **kwargs):
        created = self.pk is None

        # Set attributes before initial save
        if self.route:
            self.start_zip_code = self.route.start_zip_code

        if not self.slug:
            self.slug = slugify(self.occurence_name)

        # Save the model
        super().save(*args, **kwargs)

        # Create EventOccurenceMember if this is a new instance
        if created:
            EventOccurenceMember.objects.create(
                event_occurence=self,
                user=self.created_by,
                role=RoleType(RoleType.Creator).value,
            )

    def __str__(self):
        return f'{self.occurence_name} - {self.ride_date.strftime("%b %d %Y")}'

    class Meta:
        indexes = [
            models.Index(fields=["ride_date", "start_zip_code"]),
        ]


class EventOccurenceMemberBase(models.Model):
    user = models.ForeignKey(get_user_model(), null=True, on_delete=models.CASCADE)
    event_occurence = models.ForeignKey(
        EventOccurence,
        null=True,
        on_delete=models.CASCADE,
        related_name="%(class)s_members",
    )

    def send_event_email(self, deletor, template, subject, body, custom_message=None):
        message = render_to_string(
            template,
            {
                "body": body,
                "member": self.user,
                "deletor": deletor,
                "custom_message": custom_message,
            },
        )

        if template and send_mail(
            subject,
            "plaintext email",
            "groupvelo@gmail.com",
            [self.user.email],
            html_message=message,
        ):
            return (True, self.user)
        else:
            return (False, self.user)

    def generate_email_data(self, ride_leader, custom_message, member_list_type):
        ride_name = self.event_occurence.occurence_name
        leader_name = f"{ride_leader.name}"
        ride_name_and_date = f"{ride_name.capitalize()} on {self.event_occurence.ride_date.strftime('%-m/%-d/%Y')}"
        template = "events/emails/leader_removed_rider_email.html"

        if member_list_type == MemberListType.RIDE:
            subject = f"REGISTRATION CANCELED - {ride_name}"
            body = f"Your registration for {ride_name_and_date} has been canceled by {leader_name}"
        elif member_list_type == MemberListType.WAITLIST:
            subject = f"WAITLIST REGISTRATION CANCELED - {ride_name}"
            body = f"Your waitlist registration for {ride_name_and_date} has been canceled by {leader_name}"
        else:
            subject, body = None, None

        return subject, body, template

    def notify_member_list(
        self,
        request,
        member_list_type,
        custom_message=None,
        original_ride_date=None,
    ):
        if member_list_type == MemberListType.RIDE:
            notification_type = NotificationType.RideRegistrationDeleted
        elif member_list_type == MemberListType.WAITLIST:
            notification_type = NotificationType.WaitlistRegistrationDeleted
        else:
            notification_type = None

        deleted_member = self.user
        ride_leader = request.user

        subject, body, template = self.generate_email_data(request.user, custom_message, member_list_type)
        success, member = self.send_event_email(ride_leader, template, subject, body, custom_message)

        self.event_occurence.create_notification(deleted_member, notification_type, subject, body, custom_message)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["event_occurence", "user"], name="%(class)s_unique_user")]

        abstract = True


class EventOccurenceMemberWaitlist(EventOccurenceMemberBase):
    role = models.IntegerField(
        "Role",
        choices=list(
            filter(
                lambda role: role[1] == "Rider",
                RoleType.choices,
            )
        ),
        default=2,
    )
    waitlist_join_date = models.DateTimeField("Join Date", auto_now_add=True)

    def num_comments(self, user):
        return {"total": 0, "new": 0}

    def delete(self, *args, request=None, deleted_by_other=None, **kwargs):
        if deleted_by_other and request:
            member_list_type = MemberListType.WAITLIST
            self.notify_member_list(
                request,
                member_list_type,
            )
        return super().delete()

    def __str__(self):
        role = RoleType(self.role).label
        ride_date = self.event_occurence.ride_date.strftime("%b %d %Y")
        name = self.user.name
        event_name = self.event_occurence.occurence_name
        return f"{event_name} - {ride_date} - {name} - {role}"


class EventOccurenceMember(EventOccurenceMemberBase):
    role = models.IntegerField("Role", choices=RoleType.choices, default=2)
    attended = models.BooleanField("Attended", default=True, blank=False, null=False)

    def num_comments(self, user):
        ride_id = self.event_occurence.id

        last_comment_visit_ride = (
            EventOccurenceMessageVisit.objects.filter(user=user)
            .order_by("event_occurence", "-last_visit")
            .values("event_occurence_id", "last_visit")
            .distinct("event_occurence")
            .filter(event_occurence_id=ride_id)
        )

        last_visit = (
            datetime.datetime(1900, 1, 1, tzinfo=datetime.UTC)
            if not last_comment_visit_ride.exists()
            else last_comment_visit_ride.get(event_occurence_id=ride_id)["last_visit"]
        )

        new_messages = (
            EventOccurenceMessage.objects.filter(event_occurence=ride_id, create_date__gte=last_visit)
            .values("event_occurence")
            .annotate(total=Count("event_occurence"))
        )

        total_messages = (
            EventOccurenceMessage.objects.filter(event_occurence__id=self.event_occurence.id)
            .values("event_occurence__id")
            .annotate(total=Count("event_occurence__id"))
        )

        total_message_count = (
            0 if not total_messages.exists() else total_messages.get(event_occurence_id=ride_id)["total"]
        )

        new_message_count = 0 if not new_messages.exists() else new_messages.get(event_occurence_id=ride_id)["total"]

        return {"total": total_message_count, "new": new_message_count}

    @property
    def is_ride_leader(self):
        return self.role <= RoleType(RoleType.Leader).value

    def is_only_ride_leader(self):
        return self.is_ride_leader and self.event_occurence.ride_leaders().count() == 1

    @property
    def is_ride_creator(self):
        return self.role == RoleType(RoleType.Creator).value

    def member_is_ride_creator(self):
        return self.role == RoleType(RoleType.Creator).value

    @property
    def is_private(self):
        return self.event_occurence.privacy == EventMemberType.Members

    def clean(self, *args, **kwargs):
        if self.event_occurence is not None:
            ride_is_full(self.event_occurence)

            # prevent non-members from joining members-only ride
            if EventMemberType(self.event_occurence.privacy) is EventMemberType.Members:
                occurence_club = self.event_occurence.club
                club_membership_exists = ClubMembership.objects.filter(user=self.user, club=occurence_club).exists()
                not_member_of_club(club_membership_exists)

                membership = ClubMembership.objects.get(user=self.user, club=occurence_club)
                expiration_date = membership.membership_expires
                membership_is_expired(expiration_date.date(), self.event_occurence.ride_date)

    def delete(self, using=None, keep_parents=False, request=None, deleted_by_other=None):
        # Your custom deletion logic
        if deleted_by_other and request:
            member_list_type = MemberListType.RIDE
            self.notify_member_list(request, member_list_type)

        if self.is_only_ride_leader() and request:
            messages.error(request, "Cannot leave ride until another ride leader is appointed.")
            return (0, {})

        self.event_occurence.promote_from_waitlist_to_ride()

        return super().delete(using=using, keep_parents=keep_parents)

    def __str__(self):
        role = RoleType(self.role).label
        ride_date = self.event_occurence.ride_date.strftime("%b %d %Y")
        name = self.user.name
        event_name = self.event_occurence.occurence_name
        return f"{event_name} - {ride_date} - {name} - {role}"


class EventOccurenceMessage(models.Model):
    event_occurence = models.ForeignKey(EventOccurence, on_delete=models.CASCADE)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    message = models.TextField(blank=False)
    create_date = models.DateTimeField("Date Created", auto_now_add=True)

    @property
    def time_since_message(self):
        tz = pytz.timezone(self.event_occurence.time_zone)

        current_datetime = datetime.datetime.now(tz)
        rd = relativedelta(self.create_date, current_datetime)
        datetime_string = self.create_date.strftime("%-m/%-d/%Y - %I:%M%p")
        mins_since_comment = abs(rd.hours) * 60 + abs(rd.minutes)

        if abs(rd.days) > 0:
            return f"{datetime_string}"
        elif mins_since_comment > 60:
            return f"{abs(rd.hours)} hour{'s'[:abs(rd.hours) ^ 1]} ago"
        elif mins_since_comment == 0:
            return "just now"
        else:
            return f"{abs(rd.minutes)} minute{'s'[:abs(rd.minutes) ^ 1]} ago"

    def __str__(self):
        name = self.user.name
        create_date_string = self.create_date.strftime("%-m/%-d/%Y - %I:%M%p")
        return f"{name} - {create_date_string}"


class EventOccurenceMessageVisit(models.Model):
    event_occurence = models.ForeignKey(EventOccurence, on_delete=models.CASCADE)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    last_visit = models.DateTimeField("Date Created", auto_now_add=True)

    def __str__(self):
        last_visit_string = self.last_visit.strftime("%-m/%-d/%Y - %I:%M%p")
        return f"{self.event_occurence.occurence_name} - {last_visit_string}"
