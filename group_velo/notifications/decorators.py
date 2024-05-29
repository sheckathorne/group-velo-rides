from functools import wraps

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from sqids.sqids import Sqids

from config.settings.base import SQIDS_ALPHABET, SQIDS_MIN_LEN
from group_velo.notifications.models import Notification


def can_read_notification_for_user(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        sqids = Sqids(alphabet=SQIDS_ALPHABET, min_length=SQIDS_MIN_LEN)
        user = request.user
        notification_sqid = kwargs["notification_sqid"]
        notification_id = sqids.decode(notification_sqid)[0]

        notification = get_object_or_404(Notification, pk=notification_id)

        if notification.user == user:
            return function(request, *args, **kwargs)
        else:
            messages.error(
                request,
                "You are not authorized to view this notification",
                extra_tags={"timeout-5000"},
            )
            return HttpResponseRedirect("/")

    return wrap
