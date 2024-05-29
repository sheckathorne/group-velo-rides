from functools import wraps

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from sqids.sqids import Sqids

from config.settings.base import SQIDS_ALPHABET, SQIDS_MIN_LEN
from group_velo.clubs.models import ClubMembership
from group_velo.data.choices import MemberType


def requestor_can_manage_club(slug, user):
    member = ClubMembership.objects.filter(
        user=user,
        club__slug=slug,
        membership_type__lte=MemberType(MemberType.Admin).value,
    )
    return member.exists()


def can_manage_club(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        slug = kwargs["slug"]
        requestor_manages_club = requestor_can_manage_club(slug, request.user)

        if requestor_manages_club:
            return function(request, *args, **kwargs)
        else:
            messages.error(request, "You cannot manage this club without admin privelges.")
            return HttpResponseRedirect("/")

    return wrap


def can_manage_club_or_self(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        slug = kwargs["slug"]
        membership_sqid = kwargs["membership_sqid"]
        sqids = Sqids(alphabet=SQIDS_ALPHABET, min_length=SQIDS_MIN_LEN)
        membership_id = sqids.decode(membership_sqid)[0]
        membership = get_object_or_404(ClubMembership, pk=membership_id)

        requestor_manages_club = requestor_can_manage_club(slug, request.user)
        request_for_self = request.user == membership.user

        if requestor_manages_club or request_for_self:
            return function(request, *args, **kwargs)
        else:
            messages.error(request, "You cannot manage this membership.")
            return HttpResponseRedirect("/")

    return wrap
