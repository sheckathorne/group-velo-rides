from collections import OrderedDict
from datetime import datetime

import django_filters
from crispy_forms.bootstrap import StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Div, Field, Layout
from django import forms
from django.contrib.auth import get_user_model
from django.forms import TextInput

from group_velo.clubs.models import Club
from group_velo.data.choices import DropDesignation, GroupClassification, RoleType, SurfaceType
from group_velo.events.models import EventOccurence
from group_velo.utils.utils import css_container, dropdown, form_row, text_input


class RideForm(forms.ModelForm):
    class Meta:
        model = EventOccurence
        fields = [
            "club",
            "route",
            "group_classification",
            "surface_type",
            "drop_designation",
        ]

    def __init__(self, *args, **kwargs):
        css = css_container()
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.disable_csrf = True
        self.helper.css_container = css
        self.helper.attrs["field_class"] = "mb-0"
        self.helper.layout = Layout(
            Div(
                form_row(
                    Div(
                        form_row(
                            dropdown(
                                "club",
                                "rides",
                                width="col-span-12",
                            ),
                            Field(
                                "group_classification",
                                label="Group Classifcation",
                                wrapper_class="group_classifcation_multi_checkbox mb-3 col-span-12",
                            ),
                            dropdown(
                                "surface_type",
                                "rides",
                                width="col-span-12",
                            ),
                            dropdown(
                                "drop_designation",
                                "rides",
                                width="col-span-12",
                            ),
                            text_input(
                                "distance__lt",
                                "rides",
                                width="col-span-12",
                                css_class="distance_textbox",
                            ),
                            text_input(
                                "distance__gt",
                                "rides",
                                width="col-span-12",
                                css_class="distance_textbox",
                            ),
                        ),
                        css_class="col-span-12 my-6",
                    ),
                    Div(
                        form_row(
                            Div(
                                StrictButton(
                                    "Apply Filter",
                                    value="Filter",
                                    type="submit",
                                    css_class="w-full btn-primary-color",
                                ),
                                css_class="col-span-12",
                            ),
                            Div(
                                HTML(
                                    "<button id='clear-filter-button' type='button' "
                                    "class='clearFilterButton w-full btn-primary-color'>"
                                    "Clear Filters</button>"
                                ),
                                css_class="col-span-12",
                            ),
                            Div(
                                HTML(
                                    "<button type='button' "
                                    "@click='saveFilterModalOpen=true' "
                                    "id='save-filter-button' "
                                    "class='w-full text-white hidden btn-primary-color'>"
                                    "Save Filter</button>"
                                ),
                                css_class="col-span-12",
                            ),
                            row_id="ride-filter-parent",
                        ),
                        css_class="mt-6 col-span-12",
                    ),
                    padding_bottom="pb-2",
                    css_class="pb-2",
                )
            )
        )


def get_ride_filter(request, rides, prefix):
    return RideFilter(request.GET, queryset=rides, filter_fields=get_filter_fields(rides, prefix))


class RideFilterData:
    def __init__(self, request):
        self.ride_leader = request.GET.get("ride_leader", None)
        self.club = request.GET.get("club", None)
        self.group_classification = request.GET.getlist("group_classification", None)
        self.drop_designation = request.GET.get("drop_designation", None)
        self.surface_type = request.GET.get("surface_type", None)
        self.distance__gt = request.GET.get("distance__gt", None)
        self.distance__lt = request.GET.get("distance__lt", None)
        self.year = int(request.GET.get("year", None)) if request.GET.get("year", None) else None
        self.month = int(request.GET.get("month", None)) if request.GET.get("month", None) else None
        self.day = int(request.GET.get("day", None)) if request.GET.get("day", None) else None
        self.date = (
            datetime(self.year, self.month, self.day).strftime("%a %-m/%-d")
            if all([self.year, self.month, self.day])
            else None
        )

        self.applied_filters = [
            {
                "name": "Ride Leader",
                "param_names": ["ride_leader"],
                "param_vals": [get_user_model().objects.get(slug=self.ride_leader).name if self.ride_leader else None],
            },
            {
                "name": "Club",
                "param_names": ["club"],
                "param_vals": [Club.objects.get(slug=self.club) if self.club else None],
            },
            {
                "name": "Classification",
                "param_names": ["group_classification"],
                "param_vals": self.group_classification,
            },
            {
                "name": "Drop",
                "param_names": ["drop_designation"],
                "param_vals": ["Yes" if self.drop_designation == "1" else "No"] if self.drop_designation else None,
            },
            {
                "name": "Surface Type",
                "param_names": ["surface_type"],
                "param_vals": [x[1] for x in SurfaceType.choices if x[0] == self.surface_type]
                if self.surface_type
                else None,
            },
            {
                "name": "Distance Greater Than",
                "param_names": ["distance__gt"],
                "param_vals": [self.distance__gt],
            },
            {
                "name": "Distance Less Than",
                "param_names": ["distance__lt"],
                "param_vals": [self.distance__lt],
            },
            {
                "name": "Date",
                "param_names": ["year", "month", "day"],
                "param_vals": [self.date],
            },
        ]

        self.query_params = request.GET


class RideFilter(django_filters.FilterSet):
    def __init__(self, *args, queryset=None, filter_fields=[], **kwargs):
        super().__init__(*args, **kwargs)
        self.filters = OrderedDict()
        for field in filter_fields:
            self.filters[field[0]] = field[1]

        self.queryset = queryset

    class Meta:
        form = RideForm
        model = EventOccurence
        fields = [
            "club",
            "group_classification",
            "drop_designation",
            "surface_type",
            "route__distance",
            "eventoccurencemember_members__user",
        ]


def get_filter_fields(qs, table_prefix):
    def filter_club(queryset, _club, value):
        return queryset.filter(**{f"{table_prefix}club": value.id, f"{table_prefix}club__active": True})

    def filter_drop(queryset, _drop_designation, value):
        return queryset.filter(**{f"{table_prefix}drop_designation": value})

    def filter_surface(queryset, _surface_type, value):
        return queryset.filter(**{f"{table_prefix}surface_type": value})

    def filter_ride_leader(queryset, _name, value):
        ride_leader_value = RoleType(RoleType.Leader).value

        return queryset.filter(
            **{
                f"{table_prefix}eventoccurencemember_members__user__slug": value,
                f"{table_prefix}eventoccurencemember_members__role__lte": ride_leader_value,
            }
        )

    clubs_queryset = Club.objects.filter(pk__in=qs.values(f"{table_prefix}club"), active=True).distinct()

    drop_list = list(qs.values_list(f"{table_prefix}drop_designation", flat=True).distinct())
    drop_choices = [x for x in DropDesignation.choices if x[0] in drop_list]

    surface_list = list(qs.values_list(f"{table_prefix}surface_type", flat=True).distinct())
    surface_choices = [x for x in SurfaceType.choices if x[0] in surface_list]

    club = django_filters.ModelChoiceFilter(
        label="Club",
        lookup_expr="exact",
        field_name=f"{table_prefix}club",
        to_field_name="slug",
        queryset=clubs_queryset,
        empty_label="Select Club",
        method=filter_club,
    )

    drop_designation = django_filters.ChoiceFilter(
        label="Drop/No-drop",
        lookup_expr="exact",
        field_name=f"{table_prefix}drop_designation",
        choices=drop_choices,
        empty_label="Select Drop Designation",
        method=filter_drop,
    )

    surface_type = django_filters.ChoiceFilter(
        label="Surface Type",
        lookup_expr="exact",
        field_name=f"{table_prefix}surface_type",
        choices=surface_choices,
        empty_label="Select Surface Type",
        method=filter_surface,
    )

    group_classification = django_filters.MultipleChoiceFilter(
        field_name=f"{table_prefix}group_classification",
        lookup_expr="in",
        label="Ride Classification",
        choices=GroupClassification.choices,
        widget=forms.CheckboxSelectMultiple,
    )

    group_classification.always_filter = False

    distance__lt = django_filters.NumberFilter(
        field_name=f"{table_prefix}route__distance",
        lookup_expr="lt",
        label="Distance",
        widget=TextInput(attrs={"placeholder": "Distance Less Than"}),
    )

    distance__gt = django_filters.NumberFilter(
        field_name=f"{table_prefix}route__distance",
        lookup_expr="gt",
        label="",
        widget=TextInput(attrs={"placeholder": "Distance Greater Than"}),
    )

    ride_leader = django_filters.CharFilter(
        field_name=f"{table_prefix}members__user__slug",
        lookup_expr="exact",
        method=filter_ride_leader,
    )

    return [
        ("club", club),
        ("group_classification", group_classification),
        ("surface_type", surface_type),
        ("drop_designation", drop_designation),
        ("distance__lt", distance__lt),
        ("distance__gt", distance__gt),
        ("ride_leader", ride_leader),
    ]
