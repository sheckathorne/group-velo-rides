def valid_decimal(s):
    hash_map = {}
    for c in s:
        if not c.isnumeric() and c not in ".":
            return False
        hash_map[c] = hash_map.get(c, 0) + 1

    if hash_map.get(".", 0) > 1:
        return False
    return True


def filter_route_name(route_name, routes):
    return routes.filter(name__icontains=route_name)


def filter_created_by(created_by, routes):
    return routes.filter(created_by__name__icontains=created_by)


def filter_distance_lt(distance, routes):
    if valid_decimal(distance):
        return routes.filter(distance__lte=distance)
    return routes


def filter_distance_gt(distance, routes):
    if valid_decimal(distance):
        return routes.filter(distance__gte=distance)
    return routes


def filter_club_name(club_name, routes):
    return routes.filter(club__name__icontains=club_name)
