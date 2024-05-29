from django.contrib.auth.decorators import login_required
from django.urls import include, path

from group_velo.routes.decorators import can_modify_route

from . import views

app_name = "routes"

urlpatterns = [
    path("", views.MyRoutesView.as_view(), name="my_routes"),
    path(
        "create/",
        views.CreateRouteView.as_view(),
        name="create_route",
    ),
    path(
        "get_blank_edit_route_form/",
        login_required(views.get_blank_edit_route_form, login_url="/login"),
        name="get_blank_edit_route_form",
    ),
    path(
        "get_blank_delete_route_form/",
        login_required(views.get_blank_delete_route_form, login_url="/login"),
        name="get_blank_delete_route_form",
    ),
    path(
        "route/<str:route_sqid>/",
        include(
            [
                path(
                    "delete/",
                    views.DeleteRouteView.as_view(),
                    name="delete_route",
                ),
                path(
                    "edit/",
                    views.EditRouteView.as_view(),
                    name="edit_route",
                ),
                path(
                    "get_edit_form/",
                    login_required(can_modify_route(views.get_edit_form), login_url="/login"),
                    name="get_edit_form",
                ),
                path(
                    "get_delete_form/",
                    login_required(can_modify_route(views.get_delete_form), login_url="/login"),
                    name="get_delete_form",
                ),
            ]
        ),
    ),
]
