from django.contrib.auth.decorators import login_required
from django.urls import include, path

from group_velo.users.decorators import contact_belongs_to_requestor

from . import views
from .views import UserProfile

app_name = "users"

urlpatterns = [
    path(
        "register/",
        include(
            [
                path("", views.register, name="register"),
                path(
                    "check_email/",
                    views.register_check_email,
                    name="register_check_email",
                ),
                path(
                    "check_username/",
                    views.register_check_username,
                    name="register_check_username",
                ),
                path("check_name/", views.register_check_name, name="register_check_name"),
                path(
                    "check_zip_code/",
                    views.register_check_zip_code,
                    name="register_check_zip_code",
                ),
                path(
                    "check_password/",
                    views.register_check_password,
                    name="register_check_password",
                ),
                path(
                    "check_password_confirm/",
                    views.register_check_password_confirm,
                    name="register_check_password_confirm",
                ),
            ]
        ),
    ),
    path("login/", views.custom_login, name="login"),
    path("logout/", views.custom_logout, name="logout"),
    path("confirmation/", views.await_confirmation, name="await_confirmation"),
    path("change_password/", views.change_password, name="change_password"),
    path("password_reset/", views.reset_password_request, name="reset_password"),
    path(
        "reset/<uidb64>/<token>/",
        views.reset_password_confirm,
        name="reset_password_confirm",
    ),
    path("activate/<uidb64>/<token>/", views.activate, name="activate"),
    path(
        "blank_delete_emergency_contact_form/",
        login_required(views.get_blank_delete_emergency_contact_form, login_url="/login"),
        name="blank_delete_emergency_contact_form",
    ),
    path(
        "profile/edit/",
        include(
            [
                path(
                    "",
                    login_required(UserProfile.as_view(), login_url="/login"),
                    name="edit_profile",
                ),
                path(
                    "emergency_contact_form/",
                    login_required(views.emergency_contact_form, login_url="/login"),
                    name="emergency_contact_form",
                ),
                path(
                    "create_emergency_contact/",
                    login_required(views.create_emergency_contact, login_url="/login"),
                    name="create_emergency_contact",
                ),
                path(
                    "emergency_contacts/<str:contact_sqid>/",
                    include(
                        [
                            path(
                                "delete_emergency_contact/",
                                login_required(
                                    contact_belongs_to_requestor(views.delete_emergency_contact),
                                    login_url="/login",
                                ),
                                name="delete_emergency_contact",
                            ),
                            path(
                                "get_emergency_contact_delete_form/",
                                login_required(
                                    contact_belongs_to_requestor(views.get_delete_emergency_contact_form),
                                    login_url="/login",
                                ),
                                name="get_emergency_contact_delete_form",
                            ),
                        ]
                    ),
                ),
            ]
        ),
    ),
]
