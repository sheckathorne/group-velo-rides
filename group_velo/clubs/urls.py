from django.contrib.auth.decorators import login_required
from django.urls import include, path, re_path

from group_velo.clubs.decorators import can_manage_club, can_manage_club_or_self

from . import views

app_name = "clubs"

urlpatterns = [
    path("", views.MyClubs.as_view(), name="my_clubs"),
    path(
        "create/",
        login_required(views.CreateClubView.as_view(), login_url="/login"),
        name="create_club",
    ),
    re_path(
        r"^search(?:/(?P<zip_code>[0-9]+))?(?:/(?P<club_name>\w+))?/$",
        login_required(views.SearchClubView.as_view(), login_url="/login"),
        name="search_club",
    ),
    re_path(
        r"^membership_request/"
        r"(?P<club_sqid>.+)"
        r"(?:/(?P<latitude>[-.0-9]+))?"
        r"(?:/(?P<longitude>[-.0-9]+))?"
        r"(?:/(?P<club_name>\w+))?"
        r"(?:/(?P<zip_code>[0-9]+))?/$",
        login_required(views.create_club_membership_request, login_url="/login"),
        name="club_membership_request",
    ),
    path(
        "blank_membership_form/",
        views.get_blank_membership_form,
        name="blank_membership_form",
    ),
    path(
        "blank_membership_toggle_form/",
        views.get_blank_membership_toggle_form,
        name="blank_membership_toggle_form",
    ),
    path(
        "blank_membership_rejection_request_form/",
        views.get_blank_membership_rejection_request_form,
        name="blank_membership_rejection_request_form",
    ),
    path(
        "get_blank_club_verification_form/",
        views.get_blank_club_verification_form,
        name="get_blank_club_verification_form",
    ),
    path(
        "verification/",
        views.display_club_verification_requests,
        name="display_club_verification_requests",
    ),
    path(
        "get_blank_club_verification_response_form/",
        views.get_blank_club_verification_response_form,
        name="get_blank_club_verification_response_form",
    ),
    path(
        "<str:slug>/",
        include(
            [
                path(
                    "about/",
                    login_required(views.club_about, login_url="/login"),
                    name="club_about",
                ),
                path(
                    "edit/",
                    login_required(can_manage_club(views.EditClub.as_view()), login_url="/login"),
                    name="edit_club",
                ),
                path(
                    "save_club_verification_response/",
                    views.save_club_verification_response,
                    name="save_club_verification_response",
                ),
                path(
                    "get_club_verification_response_form/<str:response_status>/",
                    views.get_club_verification_response_form,
                    name="get_club_verification_response_form",
                ),
                path(
                    "get_club_verification_form/",
                    login_required(views.get_club_verification_form, login_url="/login"),
                    name="get_club_verification_form",
                ),
                path(
                    "create_verification_request/",
                    login_required(
                        can_manage_club(views.create_verification_request),
                        login_url="/login",
                    ),
                    name="create_verification_request",
                ),
                path(
                    "members/management/",
                    include(
                        [
                            path(
                                "edit/<str:membership_sqid>/",
                                login_required(
                                    can_manage_club(views.ClubMemberManagement.as_view()),
                                    login_url="/login",
                                ),
                                name="edit_club_member",
                            ),
                            path(
                                "create/<str:membership_request_sqid>/",
                                login_required(
                                    can_manage_club(views.create_club_member),
                                    login_url="/login",
                                ),
                                name="create_club_member",
                            ),
                            path(
                                "activation/<str:membership_sqid>/<str:tab_type>/",
                                login_required(
                                    can_manage_club_or_self(views.deactivate_membership),
                                    login_url="/login",
                                ),
                                name="club_member_activation",
                            ),
                            path(
                                "reject/<str:membership_request_sqid>/",
                                login_required(
                                    can_manage_club(views.reject_membership_request),
                                    login_url="/login",
                                ),
                                name="reject_membership_request",
                            ),
                            path(
                                "get_approval_form/<str:membership_request_sqid>/<str:form_type>/",
                                login_required(
                                    can_manage_club(views.get_membership_form),
                                    login_url="/login",
                                ),
                                name="get_membership_form",
                            ),
                            path(
                                "get_rejection_form/<str:membership_request_sqid>/",
                                login_required(
                                    can_manage_club(views.get_membership_request_rejection_form),
                                    login_url="/login",
                                ),
                                name="get_membership_request_rejection_form",
                            ),
                            path(
                                "<str:tab_type>/",
                                include(
                                    [
                                        path(
                                            "",
                                            login_required(
                                                can_manage_club(views.ClubMemberManagement.as_view()),
                                                login_url="/login",
                                            ),
                                            name="club_member_management",
                                        ),
                                        path(
                                            "<str:membership_sqid>/<str:activation_type>/",
                                            login_required(can_manage_club(views.toggle_membership)),
                                            name="toggle_membership",
                                        ),
                                    ]
                                ),
                            ),
                        ]
                    ),
                ),
            ]
        ),
    ),
]