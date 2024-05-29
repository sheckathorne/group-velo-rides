from django_unicorn.components import UnicornView
from routes.components.utils import filter_created_by, filter_distance_gt, filter_distance_lt, filter_route_name


def filter_routes(route_name, created_by, distance_lt, distance_gt, routes):
    if route_name:
        routes = filter_route_name(route_name, routes)

    if created_by:
        routes = filter_created_by(created_by, routes)

    if distance_lt:
        routes = filter_distance_lt(distance_lt, routes)

    if distance_gt:
        routes = filter_distance_gt(distance_gt, routes)

    return routes


class RouteSelectView(UnicornView):
    route_name = ""
    created_by = ""
    distance_lt = ""
    distance_gt = ""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.routes = kwargs.get("routes", None)

    def filtered_routes(self):
        routes = filter_routes(
            self.route_name,
            self.created_by,
            self.distance_lt,
            self.distance_gt,
            self.routes,
        )
        return {"routes": routes}
