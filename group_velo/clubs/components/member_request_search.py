from better_elided_pagination.paginators import BetterElidedPaginator
from django_unicorn.components import UnicornView

from group_velo.data.choices import RequestStatus


def filter_membername(name, reqs):
    return [m for m in reqs if name.lower() in m.user.name.lower()]


def filter_status(status, reqs):
    return [m for m in reqs if m.status == int(status)]


def filter_requests(name, status, reqs):
    if name:
        reqs = filter_membername(name, reqs)

    if status:
        reqs = filter_status(status, reqs)

    return reqs


def gather_status_choices(reqs):
    choices = []
    for req in reqs.values_list("status", flat=True).distinct().order_by("status"):
        choices.append({"label": RequestStatus(req).label, "value": req})
    return choices


class MemberRequestSearchView(UnicornView):
    membername = ""
    selected_status = ""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.reqs = kwargs.get("reqs", None)
        self.tab_type = kwargs.get("tab_type", None)

    def searched_requests(self):
        status_choices = gather_status_choices(self.reqs)
        members = filter_requests(self.membername, self.selected_status, self.reqs)

        pagination = BetterElidedPaginator(self.request, members, 10)
        self.call("processHtmx")

        return {
            "pagination": pagination,
            "status_choices": status_choices,
            "tab_type": self.tab_type,
        }
