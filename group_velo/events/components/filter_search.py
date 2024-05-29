from django_unicorn.components import UnicornView


def filter_club(club, filters):
    def club_filter(filter_item):
        if club == "":
            return True

        filter_dict = filter_item.filter_dict
        if "club" in filter_dict.keys():
            for club_filter_string in filter_dict["club_name"]:
                if club.lower() in club_filter_string.lower():
                    return True
        return False

    return list(filter(club_filter, filters))


def filter_classification(group_classification, filters):
    def classification_filter(filter_item):
        if group_classification == "":
            return True

        filter_dict = filter_item.filter_dict
        if "group_classification" in filter_dict.keys():
            for gc_filter_string in filter_dict["group_classification"]:
                if group_classification.lower() == gc_filter_string.lower():
                    return True
        return False

    return list(filter(classification_filter, filters))


def filter_filters(group_classification, club, filters):
    if group_classification:
        filters = filter_classification(group_classification, filters)

    if club:
        filters = filter_club(club, filters)

    return filters


class FilterSearchView(UnicornView):
    group_classification = ""
    club = ""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.saved_filters = kwargs.get("filters", None)

    def searched_filters(self):
        filters = filter_filters(self.group_classification, self.club, self.saved_filters)

        return {
            "filters": filters,
        }
