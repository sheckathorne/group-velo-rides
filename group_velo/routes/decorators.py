from functools import wraps

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from sqids.sqids import Sqids

from config.settings.base import SQIDS_ALPHABET, SQIDS_MIN_LEN
from group_velo.routes.models import Route


def can_modify_route(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        sqids = Sqids(alphabet=SQIDS_ALPHABET, min_length=SQIDS_MIN_LEN)
        route_sqid = kwargs["route_sqid"]
        route_id = sqids.decode(route_sqid)[0]
        route = get_object_or_404(Route, pk=route_id)

        if route.created_by == request.user:
            return function(request, *args, **kwargs)
        else:
            messages.error(request, "Only the route creator may edit or delete the route.")
            return HttpResponseRedirect("/")

    return wrap
