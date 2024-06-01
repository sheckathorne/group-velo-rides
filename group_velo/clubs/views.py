import os

import haversine as hs
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, ListView, TemplateView
from sqids.sqids import Sqids

from config.settings.base import SQIDS_ALPHABET, SQIDS_MIN_LEN
from group_velo.clubs.forms import (
    ClubForm,
    ClubMembership,
    ClubMembershipForm,
    ClubRideClassificationLimitForm,
    ClubSearchForm,
    ClubVerificationRequestForm,
)
from group_velo.clubs.models import Club, ClubMembershipRequest, ClubRideClassificationLimit, ClubVerificationRequest
from group_velo.data.choices import GroupClassification, MemberType, RequestStatus, SurfaceType
from group_velo.data.models import get_coords_of
from group_velo.utils.utils import get_members_by_type, search_club_context


@method_decorator(login_required(login_url="/login"), name="dispatch")
class MyClubs(ListView):
    model = Club
    DAYS_IN_FUTURE = 62
    context_object_name = "club_list"
    template_name = "clubs/my_clubs.html"

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        qs = user.clubs().order_by("-club__active", "membership_type", "club__name")
        qs = user.clubs_and_rides(qs, self.DAYS_IN_FUTURE)
        return qs

    def get_context_data(self):
        context = super().get_context_data()
        context["club_count"] = self.request.user.clubs().count()
        return context


class CreateClubView(CreateView):
    model = Club
    form_class = ClubForm
    template_name = "clubs/actions/create_club.html"
    success_url = reverse_lazy("clubs:my_clubs")

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.created_by = self.request.user
        obj.save()
        messages.success(
            self.request,
            "Successfully created your club.",
            extra_tags="timeout-5000",
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        for error in list(form.errors.values()):
            messages.error(self.request, error)
        return super().form_invalid(form)


class SearchClubView(TemplateView):
    def get(self, request, *args, zip_code=None, club_name=None, **kwargs):
        context = search_club_context(club_name, zip_code)

        if context:
            form = ClubSearchForm(initial=context)
        else:
            form = ClubSearchForm()

        return render(request, "clubs/search.html", {"form": form})

    def post(self, request):
        autoSubmit = True if request.POST.get("autoSubmit", "false") == "true" else False
        form = ClubSearchForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            club_name = data["club_name"] or None
            zip_code = data["zip_code"] or None

            (
                searched_clubs,
                latitude,
                longitude,
                include_distance,
                results_omitted,
            ) = filter_and_locate_clubs(request, None, None, zip_code, club_name)

        else:
            error_keys = list(form.errors.as_data().keys())
            if "__all__" in error_keys:
                error_keys.remove("__all__")

            field_errors = len(error_keys) > 0
            zip_code = None if not form["zip_code"].value() else form["zip_code"].value()
            club_name = None if not form["club_name"].value() else form["club_name"].value()

            if autoSubmit and not zip_code and not club_name:
                response = render_to_string(
                    "clubs/partials/_club_search_results.html",
                    {
                        "form": form,
                        "club_name": club_name,
                        "zip_code": zip_code,
                    },
                    request=request,
                )

                return HttpResponse(response)

            error_message = ""
            for error in form.errors.as_data():
                if error != "__all__":
                    for err in form.errors.as_data()[error]:
                        for e in err:
                            error_message = e
                elif error == "__all__" and not field_errors:
                    for err in form.errors.as_data()[error]:
                        for e in err:
                            error_message = e

            response = render_to_string(
                "clubs/partials/_alert_error.html",
                {
                    "error_message": error_message,
                    "close_url": reverse("notifications:remove_alert_banner"),
                },
                request=request,
            )

            return HttpResponse(response)

        response = render_to_string(
            "clubs/partials/_club_search_results.html",
            {
                "form": form,
                "searched_clubs": searched_clubs,
                "include_distance": include_distance,
                "club_name": club_name,
                "zip_code": zip_code,
                "latitude": latitude,
                "longitude": longitude,
                "results_omitted": results_omitted,
            },
            request=request,
        )

        return HttpResponse(response)


def create_club_membership_request(request, club_sqid):
    if request.method == "POST":
        sqids = Sqids(alphabet=SQIDS_ALPHABET, min_length=SQIDS_MIN_LEN)
        club_id = sqids.decode(club_sqid)[0]
        club = get_object_or_404(Club, pk=club_id)

        existing_membership_requests = ClubMembershipRequest.objects.filter(user=request.user, club=club)
        if existing_membership_requests:
            existing_membership_requests.delete()

        message = request.user.create_club_membership_request(club)

        membership_status_text = request.user.get_club_membership_request_status(club)

        rendered_template = render_to_string(
            "clubs/members/partials/_create_club_membership_request.html",
            {"message": message, "membership_status_text": membership_status_text},
        )

        return HttpResponse(rendered_template)


def deactivate_membership(request, slug, membership_sqid, tab_type):
    sqids = Sqids(alphabet=SQIDS_ALPHABET, min_length=SQIDS_MIN_LEN)
    membership_id = sqids.decode(membership_sqid)[0]
    membership = get_object_or_404(ClubMembership, pk=membership_id, club__active=True)

    # Deactivating own membership from the "my clubs" page
    if tab_type == "self_deactivation":
        # confirm the request is a self-request
        if request.user == membership.user and membership.membership_type > MemberType(MemberType.Admin).value:
            membership.active = not membership.active
            membership.save()
            messages.success(request, "Changed active status.", extra_tags="timeout-5000")
            response = HttpResponse()
            response["HX-Redirect"] = reverse("clubs:my_clubs")
            return response
        else:
            message = "You can only deactivate your own membership. Admins may not deactivate their membership."
            messages.error(request, message)
            raise ValidationError(message)

    requestor_membership = ClubMembership.objects.get(club__slug=slug, club__active=True, user=request.user)

    requestor_role = requestor_membership.membership_type
    member_role = membership.membership_type
    creator_role_type = MemberType(MemberType.Creator).value

    if member_role == creator_role_type and requestor_role > creator_role_type:
        messages.error(request, "Only creators can modify a creator.")
        raise ValidationError("Only creators can modify a creator.")
    else:
        membership.active = not membership.active
        membership.save()
        messages.success(request, "Changed active status.", extra_tags="timeout-5000")

        return redirect(
            reverse(
                "clubs:club_member_management",
                kwargs={"slug": slug, "tab_type": "active"},
            )
        )


def reject_membership_request(request, membership_request_sqid, **kwargs):
    if request.method == "POST":
        sqids = Sqids(alphabet=SQIDS_ALPHABET, min_length=SQIDS_MIN_LEN)
        membership_request_id = sqids.decode(membership_request_sqid)[0]
        membership_request = get_object_or_404(ClubMembershipRequest, pk=membership_request_id)

        membership_request.status = RequestStatus.Denied
        membership_request.responder = request.user
        membership_request.response_date = timezone.now()

        membership_request.save()
        messages.success(
            request,
            "Successfully rejected the membership request.",
            extra_tags="timeout-5000",
        )

        return redirect(request.headers["referer"])


def filter_and_locate_clubs(request, latitude, longitude, zip_code, club_name, verified=False):
    RESULT_COUNT_LIMIT = 25
    clubs = request.user.club_search_clubs(club_name)
    include_distance = False

    if zip_code:
        if not latitude and not longitude:
            latitude, longitude = get_coords_of(zip_code)

        # then calculate distance to each other club and sort by that value
        clubs = [
            {
                **club,
                "distance_between": hs.haversine(
                    (float(latitude), float(longitude)),
                    (club["latitude"], club["longitude"]),
                    unit=hs.Unit.MILES,
                ),
            }
            for club in clubs.values()
        ]

        clubs.sort(key=lambda x: x["distance_between"])
        include_distance = True

    result_count = len(clubs)

    omitted_results = result_count > RESULT_COUNT_LIMIT

    return (
        clubs[:RESULT_COUNT_LIMIT],
        latitude,
        longitude,
        include_distance,
        omitted_results,
    )


def create_club_member(request, slug, membership_request_sqid):
    sqids = Sqids(alphabet=SQIDS_ALPHABET, min_length=SQIDS_MIN_LEN)
    membership_request_id = sqids.decode(membership_request_sqid)[0]
    if request.method == "POST":
        form = ClubMembershipForm(
            request.POST,
            user=request.user,
            slug=slug,
            membership_request_id=membership_request_id,
        )

        if form.is_valid():
            membership_request = get_object_or_404(ClubMembershipRequest, pk=membership_request_id)
            club = Club.objects.get(slug=slug)
            new_club_membership = form.save(commit=False)
            new_club_membership.user = membership_request.user
            new_club_membership.club = club

            name = ""
            try:
                name = f"{membership_request.user.name}"
                new_club_membership.save()
            except IntegrityError:
                messages.error(
                    request,
                    f"Could not create club membership, {name} is already a member.",
                )
            else:
                messages.success(
                    request,
                    f"Successfully added {name} to {club.name}.",
                    extra_tags="timeout-5000",
                )

            return redirect(
                reverse(
                    "clubs:club_member_management",
                    kwargs={"slug": slug, "tab_type": "active"},
                )
            )


class ClubMemberManagement(TemplateView):
    def get(self, request, **kwargs):
        slug = kwargs["slug"]
        tab_type = kwargs.get("tab_type", None)

        club = get_object_or_404(Club, slug=slug, active=True)

        active_members = club.active_members().order_by("membership_type", "user__name")
        membership_requests = club.membership_requests().order_by("request_date")
        pending_count = club.pending_requests().count()
        members = get_members_by_type(tab_type, active_members)

        inactive_class = {
            "a": "border-b-2 border-transparent rounded-t-lg text-gray-700 hover:text-black dark:text-gray-300 "
            "dark:hover:text-white hover:border-black group",
            "svg": "text-gray-700 dark:text-gray-300 group-hover:text-black dark:group-hover:text-white",
        }

        tab_classes = {
            "active": inactive_class,
            "inactive": inactive_class,
            "requests": inactive_class,
            # change the css class of the active tab
            tab_type: {
                "a": "text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400 "
                "rounded-t-lg active group",
                "svg": "text-blue-600 dark:text-blue-400",
            },
        }

        return render(
            request=request,
            template_name="clubs/members/members_tabs.html",
            context={
                "members": members,
                "reqs": membership_requests,
                "pending_count": pending_count,
                "user": request.user,
                "slug": slug,
                "club_name": club.name,
                "club_id": club.id,
                "tab_classes": tab_classes,
                "tab_type": tab_type,
            },
        )

    @staticmethod
    def post(request, **kwargs):
        slug = kwargs["slug"]
        membership_sqid = kwargs["membership_sqid"]
        sqids = Sqids(alphabet=SQIDS_ALPHABET, min_length=SQIDS_MIN_LEN)
        membership_id = sqids.decode(membership_sqid)[0]
        club_membership = get_object_or_404(ClubMembership, pk=membership_id)

        if request.method == "POST":
            form = ClubMembershipForm(
                request.POST,
                user=request.user,
                slug=slug,
                instance=club_membership,
            )
            if form.is_valid():
                form.save()
                messages.success(
                    request,
                    "Successfully updated membership details.",
                    extra_tags="timeout-5000",
                )
                return redirect(
                    reverse(
                        "clubs:club_member_management",
                        kwargs={
                            "slug": slug,
                            "tab_type": "active",
                        },
                    )
                )
            else:
                for errortype in form.errors.as_data()["__all__"]:
                    for error in errortype:
                        messages.error(request, error)
                return redirect(
                    reverse(
                        "clubs:club_member_management",
                        kwargs={
                            "_slug": slug,
                            "tab_type": "active",
                        },
                    )
                )
        else:
            form = ClubMembershipForm(user=request.user, instance=club_membership)

        return render(
            request,
            reverse(
                "clubs:club_member_management",
                kwargs={"slug": slug, "tab_type": "active"},
            ),
            {"form": form},
        )


@login_required(login_url="/login")
def club_about(_request, slug):
    club = get_object_or_404(Club, slug=slug)

    return HttpResponse(
        render_to_string(
            "clubs/actions/modals/about_club.html",
            {
                "name": club.name,
                "description": club.description,
                "member_count": club.member_count,
                "founded_date": club.founded_date,
            },
        )
    )


def get_membership_form(request, slug, membership_request_sqid, form_type):
    sqids = Sqids(alphabet=SQIDS_ALPHABET, min_length=SQIDS_MIN_LEN)
    membership_request_id = sqids.decode(membership_request_sqid)[0]
    if form_type == "approve":
        membership_request = get_object_or_404(ClubMembershipRequest, id=membership_request_id)
        member_name = membership_request.user.name
        form_action = reverse(
            "clubs:create_club_member",
            kwargs={"slug": slug, "membership_request_sqid": membership_request_sqid},
        )
        form = ClubMembershipForm(membership_request_id=membership_request_id, slug=slug)
    else:
        club_membership = get_object_or_404(ClubMembership, id=membership_request_id)
        member_name = club_membership.user.name
        form_action = reverse(
            "clubs:edit_club_member",
            kwargs={"slug": slug, "membership_sqid": membership_request_sqid},
        )
        form = ClubMembershipForm(instance=club_membership)

    return HttpResponse(
        render_to_string(
            "clubs/members/modals/membership_form/_body.html",
            {"form": form, "member_name": member_name, "form_action": form_action},
            request=request,
        )
    )


def get_membership_request_rejection_form(request, slug, membership_request_sqid):
    sqids = Sqids(alphabet=SQIDS_ALPHABET, min_length=SQIDS_MIN_LEN)
    membership_request_id = sqids.decode(membership_request_sqid)[0]
    membership_request = get_object_or_404(ClubMembershipRequest, id=membership_request_id)
    form_action = reverse(
        "clubs:reject_membership_request",
        kwargs={"slug": slug, "membership_request_sqid": membership_request_sqid},
    )
    member_name = membership_request.user.name

    return HttpResponse(
        render_to_string(
            "clubs/members/modals/membership_request_rejection/_body.html",
            {"member_name": member_name, "form_action": form_action},
            request=request,
        )
    )


def get_blank_membership_form(request):
    return HttpResponse(render_to_string("clubs/members/modals/membership_form/_blank_body.html"))


def get_blank_membership_rejection_request_form(request):
    return HttpResponse(render_to_string("clubs/members/modals/membership_request_rejection/_blank_body.html"))


def get_blank_membership_toggle_form(request):
    return HttpResponse(render_to_string("clubs/members/modals/membership_toggle/_blank_body.html"))


def toggle_membership(request, slug, tab_type, membership_sqid, activation_type):
    sqids = Sqids(alphabet=SQIDS_ALPHABET, min_length=SQIDS_MIN_LEN)
    membership_id = sqids.decode(membership_sqid)[0]

    form_action = reverse(
        "clubs:club_member_activation",
        kwargs={"slug": slug, "membership_sqid": membership_sqid, "tab_type": tab_type},
    )
    membership = get_object_or_404(ClubMembership, id=membership_id)
    modal_title = f"{activation_type.capitalize()} Membership"
    modal_body = f"Are you sure you want to {activation_type} the membership for {membership.user.name}?"
    button_color = "btn-primary-color" if activation_type == "activate" else "btn-danger-color"

    return HttpResponse(
        render_to_string(
            "clubs/members/modals/membership_toggle/_body.html",
            {
                "form_action": form_action,
                "modal_title": modal_title,
                "modal_body": modal_body,
                "button_color": button_color,
            },
            request=request,
        )
    )


def group_classification_generator():
    for sf_count, surface_type in enumerate(SurfaceType.choices):
        gc_choices = [gc for gc in GroupClassification.choices if gc[0] != "NA"]
        for gc_count, group_classification in enumerate(gc_choices):
            first_row = gc_count == 0
            yield (
                first_row,
                surface_type,
                group_classification,
            )


class EditClub(TemplateView):
    def get(self, request, **kwargs):
        group_classification_form_list = []
        slug = kwargs["slug"]
        club = get_object_or_404(Club, slug=slug)
        existing_limits = ClubRideClassificationLimit.objects.filter(club=club)
        club_form = ClubForm(instance=club, submit_text="Save")

        for list_item in group_classification_generator():
            (first_row, surface_type, group_classification) = list_item
            prefix = f"{surface_type[0]}_{group_classification[0]}"
            existing_limit = existing_limits.filter(
                surface_type=surface_type[0],
                group_classification=group_classification[0],
                active=True,
            )
            instance = existing_limit.first() if existing_limit.exists() else None

            form = ClubRideClassificationLimitForm(
                instance=instance,
                first_row=first_row,
                group_classification=group_classification,
                surface_type=surface_type,
                club_id=club.id,
                prefix=prefix,
            )

            group_classification_form_list.append(
                {
                    "first_row": first_row,
                    "surface_type": surface_type,
                    "form": form,
                    "prefix": prefix,
                }
            )

        return render(
            request=request,
            template_name="clubs/actions/edit_club.html",
            context={
                "form": club_form,
                "slug": slug,
                "club": club,
                "group_classification_form_list": group_classification_form_list,
            },
        )

    @staticmethod
    def post(request, **kwargs):
        group_classification_form_list = []
        slug = kwargs["slug"]
        club = get_object_or_404(Club, slug=slug)
        existing_limits = ClubRideClassificationLimit.objects.filter(club=club)
        club_form = ClubForm(instance=club, submit_text="Save")

        if request.method == "POST":
            # process club form
            form_data = request.POST.copy()
            gc_form = ClubForm(form_data, request.FILES, instance=club)
            old_image = club.logo
            if gc_form.is_valid():
                Club.objects.filter(slug=slug).update(
                    edited_by=request.user,
                    edited_date=timezone.now(),
                )

                if old_image:
                    image_path = Club.image_upload_to(club, instance=old_image.path)
                    if os.path.exists(image_path) and old_image.url != "/media/default/bicycle.png":
                        os.remove(image_path)

                gc_form.save()

                # if club form is valid, move on to GC forms
                for list_item in group_classification_generator():
                    (first_row, surface_type, group_classification) = list_item
                    prefix = f"{surface_type[0]}_{group_classification[0]}"
                    existing_limit = existing_limits.filter(
                        surface_type=surface_type[0],
                        group_classification=group_classification[0],
                        active=True,
                    )
                    instance = existing_limit.first() if existing_limit.exists() else None

                    gc_form = ClubRideClassificationLimitForm(
                        request.POST,
                        instance=instance,
                        prefix=prefix,
                        surface_type=surface_type,
                        group_classification=group_classification,
                        club_id=club.id,
                    )

                    group_classification_form_list.append(gc_form)

                for f in group_classification_form_list:
                    if f.is_valid():
                        cleaned_ranges = [
                            True if f.cleaned_data["lower_pace_range"] is not None else False,
                            True if f.cleaned_data["upper_pace_range"] is not None else False,
                        ]

                        # save form if all data is entered
                        if all(cleaned_ranges):
                            f.save()

                        # delete record if data is cleared and record exists
                        if not any(cleaned_ranges):
                            club_id = f.cleaned_data["club"].id
                            surface_type = f.cleaned_data["surface_type"]
                            group_classification = f.cleaned_data["group_classification"]

                            gc = ClubRideClassificationLimit.objects.filter(
                                club__id=club_id,
                                surface_type=surface_type,
                                group_classification=group_classification,
                            )
                            gc.delete()
                    else:
                        for error in list(f.errors.values()):
                            messages.error(request, error)
                        return HttpResponseRedirect(reverse("clubs:edit_club", kwargs={"slug": slug}))

                messages.success(request, "Successfully updated the club.", extra_tags="timeout-5000")
                return HttpResponseRedirect(reverse("clubs:edit_club", kwargs={"slug": slug}))
            else:
                for error in list(gc_form.errors.values()):
                    messages.error(request, error)

        group_classification_form_list = []
        club_form = ClubForm(request.POST, request.FILES, instance=club, submit_text="Save")

        # if club form is valid, move on to GC forms
        for list_item in group_classification_generator():
            (first_row, surface_type, group_classification) = list_item
            prefix = f"{surface_type[0]}_{group_classification[0]}"
            existing_limit = existing_limits.filter(
                surface_type=surface_type[0],
                group_classification=group_classification[0],
                active=True,
            )
            instance = existing_limit.first() if existing_limit.exists() else None

            gc_form = ClubRideClassificationLimitForm(
                request.POST,
                instance=instance,
                prefix=prefix,
                surface_type=surface_type,
                group_classification=group_classification,
                club_id=club.id,
            )

            group_classification_form_list.append(
                {
                    "first_row": first_row,
                    "surface_type": surface_type,
                    "form": gc_form,
                    "prefix": prefix,
                }
            )

        return render(
            request=request,
            template_name="clubs/actions/edit_club.html",
            context={
                "form": club_form,
                "slug": slug,
                "club": club,
                "group_classification_form_list": group_classification_form_list,
            },
        )


@login_required(login_url="/login")
def get_blank_club_verification_form(request):
    template = "clubs/modals/request_club_verification/_blank_body.html"
    return HttpResponse(render_to_string(template))


@login_required(login_url="/login")
def get_club_verification_form(request, slug):
    form = ClubVerificationRequestForm()

    form_action = reverse("clubs:create_verification_request", kwargs={"slug": slug})

    response = render_to_string(
        "clubs/modals/request_club_verification/_body.html",
        {
            "form": form,
            "form_action": form_action,
        },
        request=request,
    )

    return HttpResponse(response)


def create_verification_request(request, slug):
    if request.method == "POST":
        form = ClubVerificationRequestForm(request.POST)
        if form.is_valid():
            club = get_object_or_404(Club, slug=slug)
            email = request.POST.get("contact_email", None)
            obj = form.save(commit=False)
            obj.created_by = request.user
            obj.club = club
            obj.contact_email = email
            obj.save()

            messages.success(
                request,
                "Successfully submitted your request to verify the club.",
                extra_tags="timeout-5000",
            )
        else:
            for error in list(form.errors.values()):
                messages.error(request, error)

        return HttpResponseRedirect(reverse("clubs:my_clubs"))


@login_required(login_url="/login")
@user_passes_test(lambda u: u.is_superuser)
def display_club_verification_requests(request):
    club_verification_requests = ClubVerificationRequest.objects.all()

    return render(
        request=request,
        template_name="clubs/actions/verify_club.html",
        context={"club_verification_requests": club_verification_requests},
    )


@login_required(login_url="/login")
@user_passes_test(lambda u: u.is_superuser)
def get_club_verification_response_form(request, slug, response_status):
    if response_status == "approved":
        button_color = "btn-primary-color"
        response_status = RequestStatus.Approved
        modal_body = "Are you sure you want to verify this club?"
        modal_title = "Confirm verification"
    else:
        button_color = "btn-danger-color"
        response_status = RequestStatus.Denied
        modal_body = "Are you sure you deny this verification request?"
        modal_title = "Deny verification"

    form_action = reverse("clubs:save_club_verification_response", kwargs={"slug": slug})

    response = render_to_string(
        "clubs/actions/modals/verify_club/_body.html",
        {
            "button_color": button_color,
            "response_status": response_status,
            "modal_body": modal_body,
            "modal_title": modal_title,
            "form_action": form_action,
        },
        request=request,
    )

    return HttpResponse(response)


def get_blank_club_verification_response_form(request):
    return HttpResponse(render_to_string("clubs/actions/modals/verify_club/_blank_body.html"))


@login_required(login_url="/login")
@user_passes_test(lambda u: u.is_superuser)
def save_club_verification_response(request, slug):
    if request.method == "POST":
        cvr = get_object_or_404(ClubVerificationRequest, club__slug=slug)
        status = request.POST.get("status", 1)
        responder = request.user
        response_date = timezone.now()

        cvr.status = status
        cvr.responder = responder
        cvr.response_date = response_date

        cvr.save()

        messages.success(
            request,
            "Successfully responded to the verification request",
            extra_tags="timeout-5000",
        )

    else:
        messages.warning(
            request,
            "Something went wrong, please try again.",
            extra_tags="timeout-5000",
        )

    return HttpResponseRedirect(reverse("clubs:display_club_verification_requests"))
