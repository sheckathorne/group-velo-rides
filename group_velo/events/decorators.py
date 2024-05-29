from functools import wraps

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from sqids.sqids import Sqids

from config.settings.base import SQIDS_ALPHABET, SQIDS_MIN_LEN
from group_velo.data.choices import RoleType
from group_velo.events.models import Event, EventOccurence, EventOccurenceMember
from group_velo.users.models import SavedFilter


def can_view_user_emergency_contacts(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        sqids = Sqids(alphabet=SQIDS_ALPHABET, min_length=SQIDS_MIN_LEN)
        event_occurence_sqid = kwargs["event_occurence_sqid"]
        event_occurence_id = sqids.decode(event_occurence_sqid)[0]
        user_sqid = kwargs["user_sqid"]
        user_id = sqids.decode(user_sqid)[0]

        requestor = request.user
        event_occurence = get_object_or_404(EventOccurence, pk=event_occurence_id)
        rider = get_object_or_404(get_user_model(), pk=user_id)

        requestor_is_ride_leader = (
            event_occurence.members()
            .filter(
                user=requestor,
                role__lte=RoleType(RoleType.Leader).value,
            )
            .exists()
        )

        rider_is_registered_for_ride = event_occurence.members().filter(user=rider).exists()

        if requestor_is_ride_leader and rider_is_registered_for_ride:
            return function(request, *args, **kwargs)
        else:
            messages.error(
                request,
                "You are not authorized to view this rider's emergency contact information",
                extra_tags={"timeout-5000"},
            )
            return HttpResponseRedirect("/")

    return wrap


def user_owns_saved_filter(function):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            sqids = Sqids(alphabet=SQIDS_ALPHABET, min_length=SQIDS_MIN_LEN)
            saved_filter_sqid = kwargs["saved_filter_sqid"]
            saved_filter_id = sqids.decode(saved_filter_sqid)[0]
            saved_filter = SavedFilter.objects.filter(pk=saved_filter_id, user=request.user)
            if not saved_filter.exists():
                messages.error(
                    request,
                    "You may only delete your own filters",
                    extra_tags="timeout-5000",
                )
                return redirect(reverse("homepage"))

            return view_func(request, *args, **kwargs)

        return _wrapped_view

    if function:
        return decorator(function)

    return decorator


def registration_modifier_is_leader(function):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            rider_sqid = kwargs["rider_sqid"]
            event_occurence_sqid = kwargs["event_occurence_sqid"]
            sqids = Sqids(alphabet=SQIDS_ALPHABET, min_length=SQIDS_MIN_LEN)
            rider_id = sqids.decode(rider_sqid)[0]
            event_occurence_id = sqids.decode(event_occurence_sqid)[0]

            # ensure requstor is a ride leader
            member = EventOccurenceMember.objects.filter(
                event_occurence__id=event_occurence_id,
                user=request.user,
                role__lte=RoleType(RoleType.Leader).value,
            )

            if not member.exists():
                messages.error(
                    request,
                    "You cannot modify this rider's registration unless you are a ride leader",
                )
                return redirect(reverse("events:my_rides"))

            # ensure requestor is removing a non ride creator unless the requestor is removing self
            member = EventOccurenceMember.objects.filter(
                Q(event_occurence__id=event_occurence_id),
                Q(
                    Q(
                        user__pk=rider_id,
                        role__gte=RoleType(RoleType.Leader).value,
                    )
                    | Q(user__pk=rider_id, user=request.user)
                ),
            )

            if not member.exists():
                messages.error(request, "You cannot modify this a ride creator's ride registration")
                return redirect(reverse("events:my_rides"))

            return view_func(request, *args, **kwargs)

        return _wrapped_view

    if function:
        return decorator(function)

    return decorator


def user_is_ride_member(function=None):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            sqids = Sqids(alphabet=SQIDS_ALPHABET, min_length=SQIDS_MIN_LEN)
            event_occurence_sqid = kwargs["event_occurence_sqid"]
            event_occurence_id = sqids.decode(event_occurence_sqid)[0]
            member = EventOccurenceMember.objects.filter(user=request.user, event_occurence__id=event_occurence_id)

            if not member.exists():
                messages.error(
                    request,
                    "You cannot view this until you're registered for the ride",
                )
                return redirect(reverse("events:my_rides"))

            return view_func(request, *args, **kwargs)

        return _wrapped_view

    if function:
        return decorator(function)

    return decorator


def can_view_attendees(function):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            sqids = Sqids(alphabet=SQIDS_ALPHABET, min_length=SQIDS_MIN_LEN)
            event_occurence_sqid = kwargs.get("event_occurence_sqid", "")
            event_occurence_id = sqids.decode(event_occurence_sqid)[0]
            event_occurence = get_object_or_404(EventOccurence, pk=event_occurence_id)
            user_is_ride_leader = event_occurence.user_is_ride_leader(request.user)
            club_attendence_is_private = event_occurence.club and event_occurence.club.private_ride_attendence

            if not user_is_ride_leader and club_attendence_is_private:
                messages.error(
                    request,
                    "This attendence list is private per club rules.",
                    extra_tags="timeout-5000",
                )
                return redirect(reverse("homepage"))

            return view_func(request, *args, **kwargs)

        return _wrapped_view

    if function:
        return decorator(function)

    return decorator


def can_view_waitlist(function):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            sqids = Sqids(alphabet=SQIDS_ALPHABET, min_length=SQIDS_MIN_LEN)
            event_occurence_sqid = kwargs.get("event_occurence_sqid", "")
            event_occurence_id = sqids.decode(event_occurence_sqid)[0]
            event_occurence = get_object_or_404(EventOccurence, id=event_occurence_id)
            user_is_ride_leader = event_occurence.user_is_ride_leader(request.user)
            club_waitlist_is_private = event_occurence.club and event_occurence.club.private_ride_waitlist

            if not user_is_ride_leader and club_waitlist_is_private:
                messages.error(
                    request,
                    "This waitlist is private per club rules.",
                    extra_tags="timeout-5000",
                )
                return redirect(reverse("homepage"))

            return view_func(request, *args, **kwargs)

        return _wrapped_view

    if function:
        return decorator(function)

    return decorator


def user_is_ride_leader(function):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            sqids = Sqids(alphabet=SQIDS_ALPHABET, min_length=SQIDS_MIN_LEN)
            event_occurence_sqid = kwargs.get("event_occurence_sqid", "")
            event_occurence_id = sqids.decode(event_occurence_sqid)[0]
            event_occurence = get_object_or_404(EventOccurence, id=event_occurence_id)
            user_is_ride_leader = event_occurence.user_is_ride_leader(request.user)

            if not user_is_ride_leader:
                messages.error(
                    request,
                    "Must be a ride leader to perform this action.",
                    extra_tags="timeout-5000",
                )
                return redirect(reverse("homepage"))

            return view_func(request, *args, **kwargs)

        return _wrapped_view

    if function:
        return decorator(function)

    return decorator


def user_is_event_creator(function):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            sqids = Sqids(alphabet=SQIDS_ALPHABET, min_length=SQIDS_MIN_LEN)
            event_sqid = kwargs.get("event_sqid", "")
            event_id = sqids.decode(event_sqid)[0]
            event = get_object_or_404(Event, id=event_id)
            user_is_event_creator = event.is_created_by(request.user)

            if not user_is_event_creator:
                messages.error(
                    request,
                    "Only the series creator can delete all rides. You may delete individual rides as long "
                    "as you are a ride leader.",
                    extra_tags="timeout-5000",
                )
                return redirect(reverse("homepage"))

            return view_func(request, *args, **kwargs)

        return _wrapped_view

    if function:
        return decorator(function)

    return decorator
