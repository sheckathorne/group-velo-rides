from better_elided_pagination.paginators import BetterElidedPaginator
from django_unicorn.components import UnicornView


def filter_members(membername, members):
    if membername:
        members = [m for m in members if membername.lower() in m.user.name.lower()]
    else:
        members = [m for m in members]
    return members


class MemberSearchView(UnicornView):
    membername = ""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.members = kwargs.get("members", None)
        self.tab_type = kwargs.get("tab_type", None)

    def searched_members(self):
        members = filter_members(self.membername, self.members)
        pagination = BetterElidedPaginator(self.request, members, 10)
        self.call("processHtmx")

        return {
            "members": pagination.item_list,
            "page_count": pagination.num_pages,
            "pagination_items": pagination.html_list,
            "tab_type": self.tab_type,
        }
