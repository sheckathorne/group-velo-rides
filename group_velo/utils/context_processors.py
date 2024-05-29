from group_velo.data.models import NavBarItem


def split_string(str, div):
    return list(filter(None, str.split(div)))[0]


def navbar_item_data(request):
    return {
        "navbar_items": NavBarItem.objects.filter(active=True).order_by("order"),
        "app_name": split_string(request.path, "/"),
    }
