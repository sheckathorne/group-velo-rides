import datetime

from better_elided_pagination.paginators import BetterElidedPaginator
from crispy_forms.layout import Div, Field
from crispy_tailwind.tailwind import CSSContainer
from django.db.models import Q
from django.utils import timezone


def search_club_context(club_name, zip_code):
    context = {}
    if zip_code:
        context["zip_code"] = zip_code
    if club_name:
        context["club_name"] = club_name
    return context


def binary_search(lst, n):
    lft, r = 0, len(lst) - 1
    while lft <= r:
        m = lft + ((r - lft) // 2)
        if lst[m] == n:
            return m
        elif lst[m] > n:
            r = m - 1
        else:
            lft = m + 1
    return 0


def days_from_today(n):
    return datetime.date.today() + datetime.timedelta(days=n)


def club_total_from(qs, club_name):
    return qs.get(club__name=club_name)["total"]


def club_ride_count(qs, club_name):
    return 0 if not qs.exists() else club_total_from(qs, club_name)


def distinct_errors(errors_list):
    new_list = []
    for error in errors_list:
        if error not in new_list:
            new_list.append(error)

    return new_list


def remove_page_from_url(full_path):
    if "page" not in full_path:
        return full_path
    else:
        return full_path[: full_path.find("page") - 1]


def create_pagination(f, table_prefix, page_number):
    page = BetterElidedPaginator(f.qs.order_by(f"{table_prefix}ride_date", f"{table_prefix}ride_time"), 4)
    page_obj = page.get_page(page_number)
    return page_obj


def get_members_by_type(tab_type, qs):
    now = timezone.now()

    if tab_type == "inactive":
        members = qs.filter(Q(active=False) | Q(membership_expires__lt=now))
    elif tab_type == "active":
        members = qs.filter(active=True, membership_expires__gte=now)
    else:
        members = qs.filter(active=True, membership_expires__gte=now)
    return members


def text_input(field_name, id_name, width="md:col-span-4", **kwargs):
    label = kwargs.pop("label", None)
    css_class = kwargs.pop("css_class", "")
    attrs = kwargs.pop("attrs", {})

    # if label:
    field = Field(
        field_name,
        id=f"{id_name}_create_{field_name}",
        css_class=f"w-full shadow {css_class}",
        label_class="dark:text-gray-200",
        wrapper_class=width,
        label=label,
        attrs=attrs,
    )

    return field


def dropdown(field_name, id_name, width="md:col-span-4", onchange=""):
    return Field(
        field_name,
        id=f"{id_name}_create_{field_name}",
        wrapper_class=f"{width} cursor-pointer",
        label_class="dark:text-gray-200",
        onchange=onchange,
    )


def form_row(*args, padding_bottom="pb-0", **kwargs):
    row_id = "generic-row" if "row_id" not in kwargs else kwargs["row_id"]
    return Div(*args, css_class=f"grid gap-2 md:grid-cols-12 {padding_bottom}", id=row_id)


def form_row_new(*args, padding_bottom="pb-0", **kwargs):
    row_id = "generic-row" if "row_id" not in kwargs else kwargs["row_id"]
    return Div(*args, css_class=f"w-full {padding_bottom}", id=row_id)


def get_next_month(this_month, this_year):
    return (1, this_year + 1) if this_month == 12 else (this_month + 1, this_year)


def get_prev_month(this_month, this_year):
    return (12, this_year - 1) if this_month == 1 else (this_month - 1, this_year)


def get_prev_dates(selected_year, selected_month, last_ride):
    TODAY = datetime.datetime.today()
    min_month = (TODAY.month, TODAY.year)
    max_month = (last_ride.ride_date.month, last_ride.ride_date.year)

    prev_date = None if (selected_month, selected_year) == min_month else get_prev_month(selected_month, selected_year)
    next_date = None if (selected_month, selected_year) == max_month else get_next_month(selected_month, selected_year)
    return prev_date, next_date


def base_input_style():
    return (
        "bg-white shadow focus:ring-2 focus:ring-blue-700 dark:focus:ring-blue-500 border border-gray-300 "
        "rounded py-2 px-4 block w-full appearance-none leading-normal text-gray-700 dark:text-gray-200 "
        "dark:bg-gray-700 dark:border-gray-500"
    )


def css_container():
    base_input = base_input_style()

    default_styles = {
        "text": base_input,
        "number": base_input,
        "radioselect": "form-radio peer cursor-pointer border-0 ring-2 ring-gray-600 "
        "dark:bg-transparent dark:ring-gray-300 ring-offset-2 transition-colors "
        "duration-300 ease-in-out hover:ring-blue-700 checked:bg-none "
        "checked:ring-blue-700 checked:ring-offset-2 checked:disabled:bg-slate-400 "
        "checked:disabled:ring-offset-2 dark:checked:bg-blue-700 "
        "dark:checked:ring-blue-700 dark:checked:ring-offset-2 "
        "dark:checked:disabled:bg-slate-400 dark:checked:disabled:ring-offset-2 "
        "focus:ring-offset-2 disabled:cursor-not-allowed disabled:bg-slate-50 "
        "disabled:text-slate-50 disabled:ring-slate-200 disabled:ring-offset-0 "
        "size-2 disabled:size-3 disabled:checked:size-3",
        "email": base_input,
        "url": base_input,
        "password": base_input,
        "hidden": "",
        "multiplehidden": "",
        "file": "",
        "clearablefile": "",
        "textarea": base_input,
        "date": base_input,
        "datetime": base_input,
        "time": base_input,
        "checkbox": "",
        "select": base_input,
        "nullbooleanselect": "",
        "selectmultiple": base_input,
        "checkboxselectmultiple": "",
        "multi": "",
        "splitdatetime": "text-gray-700 bg-white focus:outline border border-gray-300 leading-normal px-4 "
        "appearance-none rounded-lg py-2 focus:outline-none mr-2",
        "splithiddendatetime": "",
        "selectdate": "",
        "error_border": "border-red-500",
    }

    css = CSSContainer(default_styles)
    css -= {"text": "rounded-lg"}
    css += {"text": "rounded"}
    css.label_class = "block text-gray-700 text-sm font-bold dark:text-gray-100"
    css.option_label = (
        "text-gray-700 dark:text-gray-200 font-medium "
        "peer-disabled:opacity-70 text-sm whitespace-nowrap hover:cursor-pointer "
        "peer-disabled:cursor-not-allowed peer-disabled:text-slate-400"
    )

    return css


def pagination_css():
    return {
        "tw_base": "rounded py-2 px-4 text-center",
        "tw_enabled_hover": "hover:bg-blue-100 hover:text-gray-900 dark:hover:bg-blue-300 "
        "dark:hover:text-gray-800 hover:shadow",
        "tw_enabled_text_color": "text-gray-800 dark:text-gray-400",
        "tw_disabled": "bg-transparent text-gray-500 cursor-default focus:shadow-none",
        "tw_active": "text-white bg-blue-600 shadow-xl",
        "outer_div": "",
    }


def get_group_classification_color(group_classification_value):
    match group_classification_value:
        case "A":
            return "text-red-700 bg-red-600/30 dark:text-red-800 dark:bg-red-700/30"
        case "B":
            return "text-orange-700 bg-orange-600/30 dark:text-orange-800 dark:bg-orange-700/30"
        case "C":
            return "text-yellow-700 bg-yellow-500/30 dark:text-yellow-900 dark:bg-yellow-500/30"
        case "D":
            return "text-green-700 bg-green-600/30 dark:text-green-800 dark:bg-green-700/30"
        case "N":
            return "text-blue-700 bg-blue-600/30 dark:text-blue-800 dark:bg-blue-700/30"
        case "NA":
            return "text-gray-900 bg-gray-600/30 dark:text-gray-400 dark:bg-gray-700/30"
        case _:
            return "text-gray-900 bg-gray-600/30 dark:text-gray-400 dark:bg-gray-700/30"
