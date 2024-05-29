from better_elided_pagination.paginators import BetterElidedPaginator
from django_unicorn.components import UnicornView

from group_velo.data.choices import MemberType
from group_velo.routes.components.utils import (
    filter_club_name,
    filter_distance_gt,
    filter_distance_lt,
    filter_route_name,
)
from group_velo.routes.forms import RouteForm


def filter_routes(route_name, club_name, distance_lt, distance_gt, routes):
    if route_name:
        routes = filter_route_name(route_name, routes)

    if club_name:
        routes = filter_club_name(club_name, routes)

    if distance_lt:
        routes = filter_distance_lt(distance_lt, routes)

    if distance_gt:
        routes = filter_distance_gt(distance_gt, routes)

    return routes


class MyRoutesView(UnicornView):
    route_name = ""
    distance_lt = ""
    distance_gt = ""
    club_name = ""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.routes = kwargs.get("routes", None)

    def filtered_routes(self):
        user = self.request.user
        routes = filter_routes(
            self.route_name,
            self.club_name,
            self.distance_lt,
            self.distance_gt,
            self.routes,
        )

        if routes:
            user_clubs = user.route_clubs(MemberType.RouteContributor)
            routes = [
                {
                    "route": r,
                    "form": RouteForm(user_clubs, instance=r),
                }
                for r in routes
            ]

        pagination = BetterElidedPaginator(self.request, routes, 10)

        return {"pagination": pagination}
