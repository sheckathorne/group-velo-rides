import datetime
from datetime import timedelta

from better_elided_pagination.paginators import BetterElidedPaginator
from braces.views import FormInvalidMessageMixin
from dateutil.relativedelta import relativedelta
from django.apps import apps
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import ValidationError
from django.db.models import F, Q
from django.db.utils import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.safestring import mark_safe
from django.utils.timezone import localdate
from django.views.generic import DeleteView, TemplateView, UpdateView
from django.views.generic.base import View
from django.views.generic.edit import FormMixin
from sqids.sqids import Sqids

from config.settings.base import SQIDS_ALPHABET, SQIDS_MIN_LEN
from group_velo.clubs.models import Club
from group_velo.data.choices import MemberType, RideType, RoleType
from group_velo.events.calendar import HighlightedCalendar
from group_velo.events.decorators import (
    can_view_attendees,
    can_view_waitlist,
    registration_modifier_is_leader,
    user_is_event_creator,
    user_is_ride_leader,
    user_is_ride_member,
    user_owns_saved_filter,
)
from group_velo.events.filters import RideFilterData, get_ride_filter
from group_velo.events.forms import CreateEventForm, CreateEventOccurenceMessageForm, ModifyEventForm, SaveFilterForm
from group_velo.events.models import (
    Event,
    EventOccurence,
    EventOccurenceMember,
    EventOccurenceMemberWaitlist,
    EventOccurenceMessage,
    EventOccurenceMessageVisit,
)
from group_velo.users.models import SavedFilter
from group_velo.utils.mixins import SqidMixin
from group_velo.utils.utils import distinct_errors, get_prev_dates, pagination_css
from group_velo.weather.models import WeatherForecastDay, WeatherForecastHour
from group_velo.weather.tasks import fetch_weather_for_zip


@method_decorator(login_required(login_url="/login"), name="dispatch")
class EventView(TemplateView):
    TABLE_PREFIX = ""
    ITEMS_PER_PAGE = 8
    WEATHER_FORECAST_DAY_COUNT = 3

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.DAYS_IN_FUTURE = 62
        self.template_name = "events/layout/rides.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        filter_data = RideFilterData(self.request)
        saved_filters = self.request.user.saved_filters()
        save_filter_form = SaveFilterForm()
        context["filter_data"] = filter_data
        context["saved_filters"] = saved_filters
        context["saved_filters"] = saved_filters
        context["save_filter_form"] = save_filter_form

        rides, ride_filter, filtered_rides, ride_type = self.get_ride_data()
        events_having_forecast = self.get_events_having_forecast(filtered_rides)
        unique_zip_codes = self.get_unique_zip_codes(events_having_forecast)
        weather_data, zip_codes_to_fetch_from_api = self.get_weather_data(unique_zip_codes)

        task_ids = self.fetch_weather_data_from_api(zip_codes_to_fetch_from_api)
        self.add_weather_data_to_events(filtered_rides, events_having_forecast, task_ids, weather_data)

        calendar = self.generate_calendar(ride_filter, filtered_rides, self.TABLE_PREFIX)
        pagination = BetterElidedPaginator(
            self.request,
            filtered_rides,
            self.ITEMS_PER_PAGE,
            css_classes=pagination_css(),
        )

        if ride_type in [RideType.Registered, RideType.Waitlist]:
            for ride in pagination.item_list:
                ride.comments = ride.num_comments(user=self.request.user)

        context.update(
            {
                "form": ride_filter.form,
                "pagination": pagination,
                "calendar": calendar,
                "url_name": RideType(ride_type).label,
                "ride_type": ride_type,
            }
        )

        return context

    def filter_weather_hours(self, event_occurence, weather_data):
        hours = event_occurence.ride_rounded_start_and_end_hour()
        hours_list = [str(h) for h in range(hours[0], hours[1])]
        weather_hours = {}

        weather_hours = []

        if hours_list and weather_data:
            weather_hours = [weather_data["hours"][key] for key in hours_list]
            # weather_hours = {key: weather_data["hours"][key] for key in hours_list}

        return weather_hours

    def add_weather_data_to_events(self, filtered_rides, events_having_forecast, task_ids, weather_data):
        for event_occurence_member in filtered_rides:
            if event_occurence_member.pk in [event.pk for event in events_having_forecast]:
                event_occurence_member.event_occurence.has_forecast = True

            zip_and_date_weather = weather_data.get(
                f"{event_occurence_member.event_occurence.route.start_zip_code} "
                + f"- {event_occurence_member.event_occurence.ride_date}"
            )

            # event_weather_hours_data = {}
            # event_weather_day_data = {}
            if zip_and_date_weather:
                event_weather_hours_data = zip_and_date_weather["hours"]
                filtered_hours_data = self.filter_weather_hours(
                    event_occurence_member.event_occurence, zip_and_date_weather
                )
                if filtered_hours_data:
                    event_weather_hours_data = filtered_hours_data

                event_occurence_member.event_occurence.weather = {
                    "day": zip_and_date_weather["day"],
                    "hours": event_weather_hours_data,
                }

            # Include task ID for events that are being updated
            if event_occurence_member.event_occurence.route.start_zip_code in task_ids:
                event_occurence_member.event_occurence.weather_task_id = task_ids[
                    event_occurence_member.event_occurence.route.start_zip_code
                ]

    def get_events_having_forecast(self, filtered_rides):
        cutoff_start = localdate()
        cutoff_end = cutoff_start + timedelta(days=self.WEATHER_FORECAST_DAY_COUNT - 1)

        return filtered_rides.filter(
            **{
                f"{self.TABLE_PREFIX}ride_date__gte": cutoff_start,
                f"{self.TABLE_PREFIX}ride_date__lte": cutoff_end,
            }
        )

    def generate_calendar(self, ride_filter, filtered_rides, table_prefix):
        TODAY = datetime.datetime.today()

        selected_date = {
            "month": int(self.request.GET.get("month", TODAY.month)),
            "year": int(self.request.GET.get("year", TODAY.year)),
        }

        calendar_start_date = datetime.date(selected_date["year"], selected_date["month"], 1)
        calendar_end_date = datetime.date(selected_date["year"], selected_date["month"], 1) + relativedelta(day=31)

        last_ride = filtered_rides.last()
        if last_ride:
            if table_prefix:
                last_ride = getattr(last_ride, "event_occurence")
            prev_date, next_date = get_prev_dates(selected_date["year"], selected_date["month"], last_ride)
        else:
            prev_date, next_date = None, None

        highlighted_rides = []
        for x in ride_filter.qs.filter(
            **{
                f"{table_prefix}ride_date__gte": calendar_start_date,
                f"{table_prefix}ride_date__lte": calendar_end_date,
            }
        ):
            obj = getattr(x, "event_occurence", x)
            highlighted_rides.append(
                {
                    "ride_id": obj.id,
                    "ride_year": obj.ride_date.year,
                    "ride_month": obj.ride_date.month,
                    "ride_date": obj.ride_date.day,
                    "ride_description": obj.occurence_name
                    if not obj.club
                    else obj.occurence_name + " with " + obj.club.name,
                }
            )

        calendar = HighlightedCalendar(
            selected_date["year"],
            selected_date["month"],
            prev_date,
            next_date,
            self.request,
            highlight=highlighted_rides,
        ).formatmonth()

        return calendar

    def filter_by_day(self, filtered_rides, table_prefix):
        TODAY = datetime.datetime.today()
        if self.request.GET.get("day") and self.request.GET.get("month") and self.request.GET.get("year"):
            ride_date = datetime.date(
                int(self.request.GET.get("year", TODAY.year)),
                int(self.request.GET.get("month", TODAY.year)),
                int(self.request.GET.get("day", TODAY.year)),
            )
            return filtered_rides.filter(**{f"{table_prefix}ride_date": ride_date})
        else:
            return filtered_rides

    def get_ride_data(self):
        raise NotImplementedError("Subclasses must implement get_ride_data method")

    def get_unique_zip_codes(self, rides_with_forecast):
        if rides_with_forecast:
            distinct_zip_codes = set(
                rides_with_forecast.values_list(f"{self.TABLE_PREFIX}route__start_zip_code", flat=True).distinct()
            )

            return distinct_zip_codes
        else:
            return set()

    def get_weather_data(self, zip_codes):
        weather_data = {}
        zip_codes_to_fetch_from_api = []

        # Check cache for each zip code
        for zip_code in zip_codes:
            if WeatherForecastDay.is_fresh(zip_code):
                weather_forecast = WeatherForecastDay.get_forecast(zip_code)
                if weather_forecast:
                    for forecast_day in weather_forecast:
                        weather_data[f"{zip_code} - {forecast_day.forecast_date}"] = {"day": forecast_day, "hours": {}}
                        weather_forecast_hour = WeatherForecastHour.get_forecast_hour(
                            zip_code, forecast_day.forecast_date
                        )
                        if weather_forecast_hour:
                            for forecast_hour in weather_forecast_hour:
                                weather_data[f"{zip_code} - {forecast_day.forecast_date}"]["hours"][
                                    f"{forecast_hour.hour}"
                                ] = forecast_hour
            else:
                # Add to the list to be fetched
                zip_codes_to_fetch_from_api.append(zip_code)

        return weather_data, zip_codes_to_fetch_from_api

    def fetch_weather_data_from_api(self, zip_codes):
        # Launch Celery tasks for zip codes that need fresh data
        task_ids = {}
        if zip_codes:
            for zip_code in zip_codes:
                # Launch individual tasks and store their IDs
                task = fetch_weather_for_zip.delay(zip_code)
                task_ids[zip_code] = task.id

        return task_ids


class MyRidesView(EventView):
    TABLE_PREFIX = "event_occurence__"
    # ITEMS_PER_PAGE = 8

    def get_ride_data(self):
        rides = self.request.user.upcoming_rides(self.DAYS_IN_FUTURE).order_by("event_occurence__ride_date")
        ride_filter = get_ride_filter(self.request, rides, self.TABLE_PREFIX)
        filtered_rides = self.filter_by_day(
            ride_filter.qs.order_by(f"{self.TABLE_PREFIX}ride_date", f"{self.TABLE_PREFIX}ride_time"),
            self.TABLE_PREFIX,
        )

        return rides, ride_filter, filtered_rides, RideType.Registered


class AvailableRidesView(EventView):
    TABLE_PREFIX = ""
    # ITEMS_PER_PAGE = 8

    def get_ride_data(self):
        rides = self.request.user.available_rides(self.DAYS_IN_FUTURE)
        ride_filter = get_ride_filter(self.request, rides, self.TABLE_PREFIX)
        filtered_rides = self.filter_by_day(
            ride_filter.qs.order_by(f"{self.TABLE_PREFIX}ride_date", f"{self.TABLE_PREFIX}ride_time"),
            self.TABLE_PREFIX,
        )
        return rides, ride_filter, filtered_rides, RideType.Available


class MyWaitlistView(EventView):
    TABLE_PREFIX = "event_occurence__"
    ITEMS_PER_PAGE = 4

    def get_ride_data(self):
        rides = self.request.user.waitlisted_rides(self.DAYS_IN_FUTURE).order_by("event_occurence__ride_date")
        ride_filter = get_ride_filter(self.request, rides, self.TABLE_PREFIX)
        filtered_rides = self.filter_by_day(
            ride_filter.qs.order_by(f"{self.TABLE_PREFIX}ride_date", f"{self.TABLE_PREFIX}ride_time"),
            self.TABLE_PREFIX,
        )

        return rides, ride_filter, filtered_rides, RideType.Waitlist


@method_decorator(login_required(login_url="/login"), name="dispatch")
class BaseDeleteRideView(DeleteView, SqidMixin):
    success_url = reverse_lazy("home")

    def form_valid(self, form, *args, **kwargs):
        success_url = self.get_success_url()
        self.object = self.get_object()
        self.object.delete(request=self.request, deleted_by=self.request.user, explicit_delete=True)
        return HttpResponseRedirect(success_url)

    def get_object(self, queryset=None):
        kwarg_name = self.get_kwarg_name()
        sqid = self.kwargs[kwarg_name]
        id = self.decode_sqid(sqid)
        return get_object_or_404(self.model, pk=id)

    def get_kwarg_name(self):
        raise NotImplementedError("Subclasses must implement get_kwarg_name method")


@method_decorator(user_is_ride_leader, name="dispatch")
class DeleteEventOccurenceView(BaseDeleteRideView):
    model = EventOccurence

    def get_kwarg_name(self):
        return "event_occurence_sqid"


@method_decorator(user_is_event_creator, name="dispatch")
class DeleteEventView(BaseDeleteRideView):
    model = Event

    def get_kwarg_name(self):
        return "event_sqid"


@method_decorator(login_required(login_url="/login"), name="dispatch")
class DeleteRegistrationBaseView(SuccessMessageMixin, FormInvalidMessageMixin, SqidMixin, DeleteView):
    form_invalid_message = "Something went wrong, please try again."
    success_url = reverse_lazy("events:my_rides")

    def get_id(self):
        sqid = self.kwargs["event_occurence_sqid"]
        return self.decode_sqid(sqid)

    def get_queryset(self):
        qs = self.model.objects.filter(
            Q(event_occurence__ride_date__gte=datetime.date.today()),
            Q(event_occurence__created_by=self.request.user) | Q(user=self.request.user),
        )
        return qs

    def form_valid(self, form, *args, **kwargs):
        success_url = self.get_success_url()
        self.object = self.get_object()
        self.object.delete(request=self.request, deleted_by_other=False)
        messages.success(self.request, self.success_message)
        return HttpResponseRedirect(success_url)


class DeleteRideRegistrationView(DeleteRegistrationBaseView):
    success_message = "Successfully unregistered from ride."
    model = EventOccurenceMember

    def get_object(self, queryset=None):
        id = self.get_id()
        qs = self.get_queryset()
        lookup = {"id": id}
        return get_object_or_404(qs, **lookup)


class DeleteRideWaitlistRegistrationView(DeleteRegistrationBaseView):
    success_message = "Successfully left the waitlist."
    model = EventOccurenceMemberWaitlist

    def get_object(self, queryset=None):
        id = self.get_id()
        qs = self.get_queryset()
        lookup = {"event_occurence__id": id}
        return get_object_or_404(qs, **lookup)


@method_decorator(login_required(login_url="/login"), name="dispatch")
@method_decorator(registration_modifier_is_leader, name="dispatch")
class LeaderDeleteRegistrationViewBase(SuccessMessageMixin, FormInvalidMessageMixin, SqidMixin, DeleteView):
    form_invalid_message = "Something went wrong, please try again."

    def get_success_url(self):
        return reverse(
            "events:ride_attendees",
            kwargs={"event_occurence_sqid": self.encode_sqid(self.object.event_occurence.id)},
        )

    def get_rider(self):
        rider_id = self.decode_sqid(self.kwargs["rider_sqid"])
        return get_object_or_404(get_user_model(), pk=rider_id)

    def get_object(self, queryset=None):
        event_occurences = self.get_queryset()
        event_occurence_id = self.decode_sqid(self.kwargs["event_occurence_sqid"])
        return get_object_or_404(event_occurences, event_occurence__id=event_occurence_id)

    def form_valid(self, form, *args, **kwargs):
        success_url = self.get_success_url()
        self.object = self.get_object()
        self.object.delete(request=self.request, deleted_by_other=True)
        return HttpResponseRedirect(success_url)

    def get_queryset(self):
        raise NotImplementedError("Subclasses must implement get_queryset method")


class LeaderDeleteRideRegistrationView(LeaderDeleteRegistrationViewBase):
    success_message = "Successfully unregistered rider from ride."
    model = EventOccurenceMember

    def get_queryset(self):
        rider = self.get_rider()
        return self.model.objects.filter(event_occurence__ride_date__gte=datetime.date.today(), user=rider)


class LeaderDeleteRideWaitlistRegistrationView(LeaderDeleteRegistrationViewBase):
    success_message = "Successfully unregistered rider from waitlist."
    model = EventOccurenceMemberWaitlist

    def get_queryset(self):
        rider = self.get_rider()
        return self.model.objects.filter(
            Q(event_occurence__ride_date__gte=datetime.date.today()),
            Q(event_occurence__created_by=self.request.user),
            Q(user=rider) | Q(user=self.request.user),  # this needs testing
        )


@method_decorator(login_required(login_url="/login"), name="dispatch")
@method_decorator(registration_modifier_is_leader, name="dispatch")
class RideLeaderRoleChangeView(SuccessMessageMixin, FormInvalidMessageMixin, SqidMixin, UpdateView):
    fields = []
    model = EventOccurenceMember

    def get_success_url(self):
        return reverse(
            "events:ride_attendees",
            kwargs={"event_occurence_sqid": self.encode_sqid(self.object.event_occurence.id)},
        )

    def get_rider(self):
        rider_id = self.decode_sqid(self.kwargs["rider_sqid"])
        return get_object_or_404(get_user_model(), pk=rider_id)

    def get_object(self, queryset=None):
        event_occurences = EventOccurenceMember.objects.filter(
            event_occurence__ride_date__gte=datetime.date.today(), user=self.get_rider()
        )
        event_occurence_id = self.decode_sqid(self.kwargs["event_occurence_sqid"])
        return get_object_or_404(event_occurences, event_occurence__id=event_occurence_id)


class PromoteToRideLeaderView(RideLeaderRoleChangeView):
    success_message = "Successfully promoted rider to ride leader."
    form_invalid_message = "Cannot promote this rider, please try again."

    def form_valid(self, form):
        self.object.role = RoleType(RoleType.Leader).value
        self.object.save()
        return super().form_valid(form)


class DemoteFromRideLeader(RideLeaderRoleChangeView):
    success_message = "Successfully demoted rider from leadership."
    form_invalid_message = "Cannot demote the ride creator."

    def form_valid(self, form):
        if self.object.member_is_ride_creator():
            return super().form_invalid(form)
        else:
            self.object.role = RoleType(RoleType.Rider).value
            self.object.save()
            return super().form_valid(form)


@method_decorator(login_required(login_url="/login"), name="dispatch")
@method_decorator(can_view_waitlist, name="dispatch")
class RideWaitlistView(SqidMixin, TemplateView):
    template_name = "events/member_lists/ride_waitlist.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event_occurence_id = self.decode_sqid(kwargs["event_occurence_sqid"])
        event_occurence = get_object_or_404(EventOccurence, id=event_occurence_id)
        context["event_occurence"] = event_occurence
        context["event_members"] = event_occurence.waitlist_members()
        return context


@method_decorator(login_required(login_url="/login"), name="dispatch")
@method_decorator(user_is_ride_member, name="dispatch")
@method_decorator(can_view_attendees, name="dispatch")
class RideAttendeesView(SqidMixin, TemplateView):
    template_name = "events/member_lists/ride_attendees.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event_occurence_id = self.decode_sqid(kwargs["event_occurence_sqid"])
        event_occurence = get_object_or_404(EventOccurence, pk=event_occurence_id)
        context["event_occurence"] = event_occurence
        context["event_members"] = event_occurence.members()
        context["waitlist_members"] = event_occurence.waitlist_members()
        context["user_is_ride_leader"] = event_occurence.user_is_ride_leader(self.request.user)
        return context


@method_decorator(login_required(login_url="/login"), name="dispatch")
class CreateRegistrationBaseView(SqidMixin, FormMixin, View):
    success_url = reverse_lazy("events:available_rides")
    model = EventOccurenceMember
    success_message = ""

    def get_data(self):
        event_occurence_id = self.decode_sqid(self.kwargs["event_occurence_sqid"])
        event_occurence = get_object_or_404(EventOccurence, pk=event_occurence_id, club__active=True)
        return {
            "user": self.request.user,
            "event_occurence": event_occurence,
            "role": RoleType(RoleType.Rider).value,
        }

    def post(self, request, *args, **kwargs):
        data = self.get_data()
        obj = self.model.objects.create(**data)
        obj.save()
        messages.success(request, self.success_message)
        return super().form_valid(form=None)


class CreateWaitlistRegistrationView(CreateRegistrationBaseView):
    model = EventOccurenceMemberWaitlist
    success_message = "Successfully registered to the waitlist for this ride. You will be automatically promoted "
    "to the ride roster and notified if enough riders cancel."


class CreateRideRegistrationView(CreateRegistrationBaseView):
    model = EventOccurenceMember
    success_message = "Successfully registered to ride."


@method_decorator(login_required(login_url="/login"), name="dispatch")
class EventOccurenceCommentClickView(SqidMixin, FormMixin, View):
    success_url = None

    def dispatch(self, request, *args, **kwargs):
        event_occurrence_sqid = self.kwargs.get("event_occurence_sqid")  # Get the event occurrence SQID
        self.success_url = reverse_lazy("events:ride_comments", args=[event_occurrence_sqid]) + "?sort=desc"
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        event_occurence_id = self.decode_sqid(self.kwargs["event_occurence_sqid"])
        queryset = EventOccurence.objects.filter(
            Q(pk=event_occurence_id), (Q(club__active=True) | Q(club__isnull=True))
        )
        event_occurence = get_object_or_404(queryset)

        data = {
            "user": request.user,
            "event_occurence": event_occurence,
        }
        EventOccurenceMessageVisit.objects.update_or_create(**data, defaults={"last_visit": timezone.now()})
        return super().form_valid(form=None)


@method_decorator(login_required(login_url="/login"), name="dispatch")
@method_decorator(user_is_ride_member, name="dispatch")
class EventComments(SqidMixin, TemplateView):
    template_name = "events/comments/ride_comments.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pagination"] = self.pagination
        context["event"] = self.event_occurence
        context["form"] = self.form
        context["sort"] = self.sort
        context["event_occurence_sqid"] = self.event_occurence_sqid
        return context

    def get(self, request, *args, **kwargs):
        self.event_occurence_sqid = kwargs.get("event_occurence_sqid", "")
        event_occurence_id = self.decode_sqid(self.event_occurence_sqid)
        self.sort = request.GET.get("sort", "asc")
        sort_asc = self.sort == "asc"

        self.form = CreateEventOccurenceMessageForm()
        queryset = EventOccurence.objects.filter(
            Q(pk=event_occurence_id), (Q(club__active=True) | Q(club__isnull=True))
        )

        self.event_occurence = get_object_or_404(queryset)
        sorted_and_colored_comments = self.event_occurence.sorted_and_colored_comments(sort_asc=sort_asc)
        self.pagination = BetterElidedPaginator(request, sorted_and_colored_comments, 5)
        return super().get(request, *args, **kwargs)

    def post(self, request, **kwargs):
        event_occurence_sqid = kwargs.get("event_occurence_sqid", "")
        event_occurence_id = self.decode_sqid(event_occurence_sqid)
        events = EventOccurence.objects.filter(Q(id=event_occurence_id), (Q(club__active=True) | Q(club__isnull=True)))

        event = get_object_or_404(events)

        form_data = CreateEventOccurenceMessageForm(request.POST)
        if form_data.is_valid():
            data = {
                "message": form_data["message"].value(),
                "user": request.user,
                "event_occurence": event,
            }

            click_data = {
                "user": request.user,
                "event_occurence": event,
            }

            EventOccurenceMessage.objects.create(**data)
            EventOccurenceMessageVisit.objects.update_or_create(**click_data, defaults={"last_visit": timezone.now()})

            return HttpResponseRedirect(reverse("events:ride_comments", args=[event_occurence_sqid]))
        else:
            messages.error(request, "Comment cannot be blank.")
        return HttpResponseRedirect(reverse("events:ride_comments", args=[event_occurence_sqid]))


class CreateEvent(TemplateView):
    def get(self, request, **kwargs):
        user = request.user
        user_routes = user.self_and_club_routes()
        user_clubs = user.route_clubs(MemberType.RideLeader)

        if not user_routes.exists():
            messages.warning(
                request,
                mark_safe(
                    "Cannot create event without any routes added. Please <a class='underline text-blue-600 "
                    f"hover:text-blue-800 visited:text-purple-600' href={reverse('routes:create_route')}>create a "
                    "route</a> first."
                ),
            )
            return HttpResponseRedirect("/")
        else:
            form = CreateEventForm(user_clubs, user_routes)

            return render(
                request=request,
                template_name="events/create_event.html",
                context={
                    "form": form,
                    "user_routes": user_routes,
                },
            )

    @staticmethod
    def post(request):
        user = request.user
        user_routes = user.self_and_club_routes()
        user_clubs = user.route_clubs(MemberType.RideLeader)
        form = CreateEventForm(user_clubs, user_routes, request.POST)

        if form.is_valid():
            new_event = form.save(commit=False)
            club = None if form["club"].value() == "" else Club.objects.get(pk=form["club"].value())
            new_event.club = club
            new_event.created_by = request.user

            new_event.save()

            messages.success(
                request,
                "Successfully created your ride.",
                extra_tags="timeout-5000",
            )
            return HttpResponseRedirect(reverse("events:my_rides"))
        else:
            for field, errors in form.errors.items():
                for e in errors:
                    messages.error(request, e)

            form = CreateEventForm(user_clubs, user_routes, request.POST)

            return render(
                request=request,
                template_name="events/create_event.html",
                context={
                    "form": form,
                    "user_routes": user_routes,
                },
            )


@method_decorator(login_required(login_url="/login"), name="dispatch")
@method_decorator(user_is_ride_leader, name="dispatch")
class ModifyEvent(SqidMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        event_occurence_sqid = kwargs.get("event_occurence_sqid", "")
        event_occurence_id = self.decode_sqid(event_occurence_sqid)
        event_occurence = get_object_or_404(EventOccurence.objects.select_related("route"), pk=event_occurence_id)

        registered_rider_count = event_occurence.registered_rider_count()

        user = request.user
        user_routes = user.self_and_club_routes()
        user_clubs = user.route_clubs(MemberType.RideLeader)

        if not user_routes.exists():
            messages.warning(
                request,
                "Cannot modify ride without any routes added. Please create a route first.",
            )
            return HttpResponseRedirect("/")
        else:
            form = ModifyEventForm(
                user_clubs,
                user_routes,
                registered_rider_count,
                instance=event_occurence,
            )

            return render(
                request=request,
                template_name="events/modify_event.html",
                context={
                    "form": form,
                    "user_routes": user_routes,
                    "event_occurence": event_occurence,
                },
            )

    def post(self, request, **kwargs):
        event_occurence_sqid = kwargs.get("event_occurence_sqid", "")
        event_occurence_id = self.decode_sqid(event_occurence_sqid)
        event_occurence = get_object_or_404(EventOccurence.objects.select_related("route"), pk=event_occurence_id)

        registered_rider_count = event_occurence.registered_rider_count()
        user = request.user
        user_routes = user.self_and_club_routes()
        user_clubs = user.route_clubs(MemberType.RideLeader)

        form = ModifyEventForm(
            user_clubs,
            user_routes,
            registered_rider_count,
            request.POST,
            instance=event_occurence,
        )
        if form.is_valid():
            modified_occurence = form.save(commit=False)
            modified_occurence.modified_by = user
            modified_occurence.save()

            messages.success(
                request,
                "Successfully modified your ride.",
                extra_tags="timeout-5000",
            )

            return HttpResponseRedirect(reverse("events:my_rides"))
        else:
            errors = distinct_errors(form.errors.values())
            for error in errors:
                messages.error(request, error)

            form = ModifyEventForm(
                user_clubs,
                user_routes,
                registered_rider_count,
                instance=event_occurence,
            )

            return render(
                request=request,
                template_name="events/modify_event.html",
                context={
                    "form": form,
                    "user_routes": user_routes,
                    "event_occurence": event_occurence,
                },
            )


@login_required(login_url="/login")
def get_ride_classification_limits(request):
    classification_limit = apps.get_model("clubs.ClubRideClassificationLimit")
    club = apps.get_model("clubs.Club")

    club_id = request.GET.get("club_id", None)

    surface_type = request.GET.get("surface_type", None)
    group_classification = request.GET.get("group_classification", None)

    selected_club = club.objects.get(id=club_id)

    data = classification_limit.objects.filter(
        club=selected_club,
        surface_type=surface_type,
        group_classification=group_classification,
        active=True,
    ).values(
        "lower_pace_range",
        "upper_pace_range",
        strict_ride_classification=F("club__strict_ride_classification"),
    )

    if data.exists():
        data = data.first()
        data_dict = {
            "lower_pace_range": str(data["lower_pace_range"]),
            "upper_pace_range": str(data["upper_pace_range"]),
            "strict_ride_classification": data["strict_ride_classification"],
        }
    else:
        data_dict = {
            "lower_pace_range": "0",
            "upper_pace_range": "0",
            "strict_ride_classification": False,
        }

    return JsonResponse(
        data_dict,
        safe=True,
    )


@login_required(login_url="/login")
def get_leave_waitlist_form(request, event_occurence_sqid):
    template = "events/modals/ride_registration/_body.html"
    form_action = reverse(
        "events:delete_waitlist_registration",
        kwargs={"event_occurence_sqid": event_occurence_sqid},
    )
    return HttpResponse(
        render_to_string(
            template,
            {
                "form_action": form_action,
                "body_text": "Are you sure you want to leave the waitlist for this ride?",
                "title_text": "Cancel Waitlist Registration",
                "button_color": "btn-danger-color",
            },
            request=request,
        )
    )


@login_required(login_url="/login")
def get_leave_ride_form(request, event_occurence_sqid):
    template = "events/modals/ride_registration/_body.html"
    form_action = reverse(
        "events:delete_registration",
        kwargs={"event_occurence_sqid": event_occurence_sqid},
    )
    return HttpResponse(
        render_to_string(
            template,
            {
                "form_action": form_action,
                "body_text": "Are you sure you want to cancel your registration for this ride?",
                "title_text": "Cancel Registration",
                "button_color": "btn-danger-color",
            },
            request=request,
        )
    )


@login_required(login_url="/login")
def get_join_ride_form(request, event_occurence_sqid):
    template = "events/modals/ride_registration/_body.html"
    form_action = reverse(
        "events:create_registration",
        kwargs={"event_occurence_sqid": event_occurence_sqid},
    )
    return HttpResponse(
        render_to_string(
            template,
            {
                "form_action": form_action,
                "body_text": "Are you sure you want to register for this ride?",
                "title_text": "Confirm Registration",
                "button_color": "btn-primary-color",
            },
            request=request,
        )
    )


@login_required(login_url="/login")
def get_join_waitlist_form(request, event_occurence_sqid):
    template = "events/modals/ride_registration/_body.html"
    form_action = reverse(
        "events:create_waitlist_registration",
        kwargs={"event_occurence_sqid": event_occurence_sqid},
    )
    return HttpResponse(
        render_to_string(
            template,
            {
                "form_action": form_action,
                "body_text": "Are you sure you want to join the waitlist for this ride? "
                "You will automatically be registered and notified if space becomes available.",
                "title_text": "Confirm Waitlist Registration",
                "button_color": "btn-primary-color",
            },
            request=request,
        )
    )


@login_required(login_url="/login")
def get_blank_leave_list_form(request):
    template = "events/modals/ride_registration/_blank_body.html"
    return HttpResponse(render_to_string(template))


@login_required(login_url="/login")
def get_cancel_event_form(request, event_sqid):
    sqids = Sqids(alphabet=SQIDS_ALPHABET, min_length=SQIDS_MIN_LEN)
    event_id = sqids.decode(event_sqid)[0]
    event = get_object_or_404(Event, id=event_id)
    event_occurences = event.occurences_with_rider_count()

    event_occurences_html = render_to_string(
        "events/modals/partials/_event_occurences_fragment.html",
        {
            "event_occurences": event_occurences,
            "occurence_count": event_occurences.count(),
        },
    )

    form_action = reverse("events:delete_event", kwargs={"event_sqid": event_sqid})

    response = render_to_string(
        "events/modals/cancel_event/_body.html",
        {"event_occurences_html": event_occurences_html, "form_action": form_action},
        request=request,
    )
    return HttpResponse(response)


@login_required(login_url="/login")
def get_blank_cancel_event_form(request):
    template = "events/modals/cancel_event/_blank_body.html"
    return HttpResponse(render_to_string(template))


@login_required(login_url="/login")
def get_cancel_event_occurence_form(request, event_occurence_sqid):
    form_action = reverse(
        "events:delete_event_occurence",
        kwargs={"event_occurence_sqid": event_occurence_sqid},
    )
    response = render_to_string(
        "events/modals/cancel_event_occurence/_body.html",
        {"form_action": form_action},
        request=request,
    )

    return HttpResponse(response)


@login_required(login_url="/login")
def get_blank_cancel_event_occurence_form(request):
    template = "events/modals/cancel_event_occurence/_blank_body.html"
    return HttpResponse(render_to_string(template))


@login_required(login_url="/login")
def get_demote_rider_form(request, rider_sqid, event_occurence_sqid):
    form_action = reverse(
        "events:demote_from_ride_leader",
        kwargs={
            "rider_sqid": rider_sqid,
            "event_occurence_sqid": event_occurence_sqid,
        },
    )

    response = render_to_string(
        "events/modals/promote_demote_rider/_body.html",
        {
            "form_action": form_action,
            "action_text": "demote",
            "button_color": "btn-danger-color",
        },
        request=request,
    )

    return HttpResponse(response)


@login_required(login_url="/login")
def get_promote_rider_form(request, rider_sqid, event_occurence_sqid):
    form_action = reverse(
        "events:promote_to_ride_leader",
        kwargs={
            "rider_sqid": rider_sqid,
            "event_occurence_sqid": event_occurence_sqid,
        },
    )

    response = render_to_string(
        "events/modals/promote_demote_rider/_body.html",
        {
            "form_action": form_action,
            "action_text": "promote",
            "button_color": "btn-primary-color",
        },
        request=request,
    )

    return HttpResponse(response)


@login_required(login_url="/login")
def get_kick_rider_form(request, rider_sqid, event_occurence_sqid):
    form_action = reverse(
        "events:leader_delete_ride_registration",
        kwargs={
            "rider_sqid": rider_sqid,
            "event_occurence_sqid": event_occurence_sqid,
        },
    )

    response = render_to_string(
        "events/modals/promote_demote_rider/_body.html",
        {
            "form_action": form_action,
            "action_text": "remove",
            "button_color": "btn-danger-color",
        },
        request=request,
    )

    return HttpResponse(response)


@login_required(login_url="/login")
def get_promote_demote_rider_disabled_button(request):
    template = "events/modals/promote_demote_rider/_blank_body.html"
    return HttpResponse(render_to_string(template))


@login_required(login_url="/login")
@user_is_ride_leader
def user_emergency_contacts(request, user_sqid, **kwargs):
    sqids = Sqids(alphabet=SQIDS_ALPHABET, min_length=SQIDS_MIN_LEN)
    user_id = sqids.decode(user_sqid)[0]
    user = get_object_or_404(get_user_model(), pk=user_id)
    emergency_contacts = user.emergency_contacts()

    response = render_to_string(
        "events/modals/emergency_contacts_list.html",
        {
            "emergency_contacts": emergency_contacts,
            "hide_remove_button": True,
            "request": request,
        },
    )
    return HttpResponse(response)


@login_required(login_url="/login")
@user_owns_saved_filter
def delete_filter(request, saved_filter_sqid):
    sqids = Sqids(alphabet=SQIDS_ALPHABET, min_length=SQIDS_MIN_LEN)
    saved_filter_id = sqids.decode(saved_filter_sqid)[0]
    saved_filter = get_object_or_404(SavedFilter, id=saved_filter_id)
    if request.method == "DELETE":
        if saved_filter.delete():
            response = ""
            return HttpResponse(response)
    messages.error(request, "There was an unexpected problem", extra_tags="timeout-5000")
    return HttpResponseRedirect(reverse("homepage"))


@login_required(login_url="/login")
def save_filter(request):
    if request.method == "POST":
        form = SaveFilterForm(request.POST)
        if form.is_valid():
            params = {}
            for k in request.POST.keys():
                if k != "csrfmiddlewaretoken" and k != "name":
                    param_list = request.POST.getlist(k)
                    if k == "club":
                        club_name = [Club.objects.get(slug=c).name for c in param_list]
                        params["club_name"] = club_name

                    if param_list[0]:
                        params[k] = request.POST.getlist(k)

            user = request.user
            name = form.cleaned_data["name"]
            data = {"user": user, "name": name, "filter_dict": params}
            saved_filter = SavedFilter(**data)

            try:
                saved_filter.clean()
            except ValidationError as e:
                messages.warning(request, e.message, extra_tags="timeout-5000")
            else:
                try:
                    saved_filter.save()
                except IntegrityError as e:
                    error_message = str(e)
                    if "name" in error_message:
                        messages.error(
                            request,
                            "You have a filter with this name already, please choose a new name.",
                            extra_tags="timeout-5000",
                        )
                    elif "filter" in error_message:
                        messages.error(
                            request,
                            "You have this filter saved already with a different name.",
                            extra_tags="timeout-5000",
                        )
                    else:
                        messages.error(request, error_message, extra_tags="timeout-5000")
                else:
                    messages.success(
                        request,
                        "Succesfully saved your filter.",
                        extra_tags="timeout-5000",
                    )
        else:
            for error in list(form.errors.values()):
                messages.error(request.error, "There was an unexpected problem, please try again.")
        return HttpResponseRedirect(request.headers["referer"])
    return HttpResponseRedirect(request.headers["referer"])


@login_required(login_url="/login")
def get_weather_data_for_zip_and_date(request):
    zip_code = request.GET.get("zip_code")
    event_date = request.GET.get("event_date")
    task_id = request.GET.get("task_id")

    if zip_code and event_date:
        try:
            weather_data = WeatherForecastDay.objects.get(zip_code=zip_code, forecast_date=event_date)
            condition_text = weather_data.condition_text
            condition_code = weather_data.condition_code
            mintemp_c = weather_data.mintemp_c
            maxtemp_c = weather_data.maxtemp_c
            mintemp_f = weather_data.mintemp_f
            maxtemp_f = weather_data.maxtemp_f

            response = render_to_string(
                "events/ride_card/weather/_day.html",
                {
                    "condition_text": condition_text,
                    "condition_code": condition_code,
                    "mintemp_c": mintemp_c,
                    "maxtemp_c": maxtemp_c,
                    "mintemp_f": mintemp_f,
                    "maxtemp_f": maxtemp_f,
                },
            )
            return HttpResponse(response)
        except WeatherForecastDay.DoesNotExist:
            # In case the data isn't available yet, show the loading spinner again
            response = render_to_string(
                "events/ride_card/weather/_loading_day.html",
                {"task_id": task_id, "zip_code": zip_code, "event_date": event_date},
            )
            return HttpResponse(response)
    else:
        return HttpResponse("", content_type="text/html")
