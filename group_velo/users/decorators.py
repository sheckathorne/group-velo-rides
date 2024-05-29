from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from sqids.sqids import Sqids

from config.settings.base import SQIDS_ALPHABET, SQIDS_MIN_LEN
from group_velo.users.models import EmergencyContact


def contact_belongs_to_requestor(function=None):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            sqids = Sqids(alphabet=SQIDS_ALPHABET, min_length=SQIDS_MIN_LEN)
            contact_sqid = kwargs.get("contact_sqid", "")
            contact_id = sqids.decode(contact_sqid)[0]
            emergency_contact = EmergencyContact.objects.filter(id=contact_id, contact_for=request.user)

            if emergency_contact.count() < 1:
                messages.error(request, "You cannot delete this rider's emergency conatct")
                return redirect(reverse("events:my_rides"))

            return view_func(request, *args, **kwargs)

        return _wrapped_view

    if function:
        return decorator(function)
    return decorator


def user_not_authenticated(function=None, redirect_url="/"):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_authenticated:
                return redirect(redirect_url)

            return view_func(request, *args, **kwargs)

        return _wrapped_view

    if function:
        return decorator(function)
    return decorator
