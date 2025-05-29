from crispy_forms.bootstrap import InlineCheckboxes, StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Div, Field, Layout
from dateutil.relativedelta import relativedelta
from django import forms
from django.apps import apps
from django.forms import ModelChoiceField, Select
from django.utils.html import mark_safe

from group_velo.data.choices import EventMemberType, RecurrenceFrequency
from group_velo.events.models import (
    Event,
    EventOccurence,
    EventOccurenceMember,
    EventOccurenceMemberWaitlist,
    EventOccurenceMessage,
)
from group_velo.events.validators import MaxRidersValidator
from group_velo.routes.models import Route
from group_velo.users.models import SavedFilter
from group_velo.utils.forms import BaseForm
from group_velo.utils.utils import base_input_style, css_container, form_row, text_input


class DeleteRouteForm(forms.ModelForm):
    class Meta:
        model = Route
        fields = []


class DeleteRideRegistrationForm(forms.ModelForm):
    class Meta:
        model = EventOccurenceMember
        fields = []


class DeleteWaitlistRegistrationForm(forms.ModelForm):
    class Meta:
        model = EventOccurenceMemberWaitlist
        fields = []


class CreateRideRegistrationForm(forms.ModelForm):
    class Meta:
        model = EventOccurenceMember
        fields = []


class CreateEventOccurenceMessageForm(forms.ModelForm):
    class Meta:
        model = EventOccurenceMessage
        fields = ["message"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["message"].label = ""
        self.helper = FormHelper(self)
        self.helper.css_container = css_container()
        self.helper.layout = Layout(
            form_row(
                Field("message", wrapper_class="col-span-12 shadow-lg"),
                padding_bottom="pb-4",
            ),
            Div(
                StrictButton(
                    "Add Comment",
                    value="Add",
                    type="submit",
                    css_class="w-full btn-primary-color rounded shadow-lg mb-4 py-2",
                ),
            ),
        )


class SaveFilterForm(forms.ModelForm):
    class Meta:
        model = SavedFilter
        fields = ["name"]

    name = forms.CharField(
        label="Filter Name",
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "Enter filter name"}),
    )

    def __init__(self, *args, **kwargs):
        width = "col-span-12"
        row_padding = "pb-2"
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.css_container = css_container()
        self.helper.layout = Layout(
            form_row(
                text_input("name", "events:save_filter", label="Filter Name", width=width),
                padding_bottom=row_padding,
            ),
        )


class SelectWithOptionAttribute(Select):
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        if isinstance(label, dict):
            opt_attrs = label.copy()
            label = opt_attrs.pop("label")
        else:
            opt_attrs = {}

        option_dict = super().create_option(name, value, label, selected, index, subindex=subindex, attrs=attrs)

        for key, val in opt_attrs.items():
            option_dict["attrs"][key] = val

        return option_dict


class RouteChoiceField(ModelChoiceField):
    widget = SelectWithOptionAttribute(attrs={"class": base_input_style()})

    def label_from_instance(self, obj):
        return {"label": super().label_from_instance(obj), "data-url": obj.url}


class BaseEventForm(BaseForm):
    def __init__(self, *args, user_clubs=None, user_routes=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.general_header = {
            "header_svg": self.svgs["location"],
            "header_title": "Ride Information",
            "header_subtitle": "Basic details about your ride",
            "colors": self.header_colors["purple"],
        }

        self.ride_details_header = {
            "header_svg": self.svgs["general"],
            "header_title": "Ride Details",
            "header_subtitle": "More detailed information about the pace, surface type, etc.",
            "colors": self.header_colors["blue"],
        }

        self.schedule_header = {
            "header_svg": self.svgs["calendar"],
            "header_title": "Schedule & Timing",
            "header_subtitle": "Set the start and end dates, time zone, ride duration, and recurrence for the event",
            "colors": self.header_colors["orange"],
        }

        if user_clubs is not None:
            self.fields["club"].choices = user_clubs
        if user_routes is not None:
            self.fields["route"].queryset = user_routes

        self.helper = FormHelper(self)
        self.helper.css_container = css_container()
        self.helper.label_class = "block text-gray-700 text-sm font-bold dark:text-gray-100"


class ModifyEventForm(BaseEventForm):
    def __init__(self, user_clubs, user_routes, registered_rider_count, *args, **kwargs):
        super().__init__(*args, user_clubs=user_clubs, user_routes=user_routes, **kwargs)

        self.fields["max_riders"].validators.append(MaxRidersValidator(registered_rider_count))
        self.helper.layout = Layout(
            # Section 1
            Div(
                # Section Header
                self.section_header(self.general_header),
                # Section Body
                self.section_wrapper(
                    Field(
                        "occurence_name",
                        id="event_occurence_create_occurence_name",
                        css_class=self.css_class,
                        label_class=self.label_class,
                    ),
                    Field(
                        "description",
                        id="event_occurence_create_description",
                        css_class=self.css_class,
                        label_class=self.label_class,
                    ),
                    Field(
                        "privacy",
                        id="event_occurence_create_privacy",
                        css_class=self.css_class,
                        label_class=self.label_class,
                    ),
                    Field(
                        "club",
                        id="event_create_club",
                        css_class=self.css_class,
                        label_class=self.label_class,
                    ),
                    form_row(
                        Div(
                            HTML(
                                "<label for='routeChoiceButton' class='block text-gray-700 dark:text-gray-200 "
                                "text-sm font-bold'>Route<span class='asteriskField'>*</span></label>"
                            ),
                            StrictButton(
                                "Select Route",
                                css_id="routeChoiceButton",
                                css_class="w-full py-3 px-4 font-semibold btn-primary-color rounded shadow-lg",
                                **{"@click": "routeSelectModalOpen=true"},
                            ),
                            css_id="div_id_route_select",
                            css_class="col-span-12",
                        ),
                        padding_bottom="pb-2 mb-3",
                    ),
                    Field("route", type="hidden", id="route_id"),
                    Field(
                        "max_riders",
                        id="event_occurence_create_max_riders",
                        css_class=self.css_class,
                        label_class=self.label_class,
                    ),
                ),
                css_class="md:col-span-2 bg-white dark:bg-gray-900 rounded-lg "
                "overflow-hidden border border-gray-200 dark:border-gray-800 shadow-md",
            ),
            # Section 2
            Div(
                # Section Header
                self.section_header(self.ride_details_header),
                # Section Body
                self.section_wrapper(
                    Field(
                        "surface_type",
                        id="event_occurence_create_surface_type",
                        css_class=self.css_class,
                        label_class=self.label_class,
                    ),
                    Field(
                        "group_classification",
                        id="event_create_group_classification",
                        css_class=self.css_class,
                        label_class=self.label_class,
                    ),
                    Field(
                        "lower_pace_range",
                        id="event_create_lower_pace_range",
                        css_class=self.css_class,
                        label_class=self.label_class,
                    ),
                    HTML(
                        '<p x-show="lower_pace_range.errorMessage" x-text="lower_pace_range.errorMessage" '
                        ' class="-mt-4 mb-3 text-sm text-red-700 dark:text-red-400"></p>'
                    ),
                    Field(
                        "upper_pace_range",
                        id="event_create_upper_pace_range",
                        css_class=self.css_class,
                        label_class=self.label_class,
                    ),
                    HTML(
                        '<p x-show="upper_pace_range.errorMessage" x-text="upper_pace_range.errorMessage" '
                        ' class="-mt-4 mb-3 text-sm text-red-700 dark:text-red-400"></p>'
                    ),
                    Field(
                        "drop_designation",
                        id="event_occurence_create_drop_designation",
                        css_class=self.css_class,
                        label_class=self.label_class,
                    ),
                ),
                css_class="rounded-lg bg-card text-card-foreground shadow-sm border dark:border-slate-700",
            ),
            # Section 3
            Div(
                # Section Header
                self.section_header(self.schedule_header),
                # Section Body
                self.section_wrapper(
                    Field(
                        "ride_date",
                        id="event_occurence_create_ride_date",
                        css_class=self.css_class,
                        label_class=self.label_class,
                    ),
                    Field(
                        "ride_time",
                        id="event_create_ride_time",
                        css_class=self.css_class,
                        label_class=self.label_class,
                    ),
                    Field(
                        "time_zone",
                        id="event_create_time_zone",
                        css_class=self.css_class,
                        label_class=self.label_class,
                    ),
                ),
                css_class="rounded-lg bg-card text-card-foreground shadow-sm border dark:border-slate-700",
            ),
            StrictButton(
                "Save Changes",
                value="Save",
                type="submit",
                css_class="w-full bg-green-500 hover:bg-green-600 text-white font-semibold py-2 px-4 "
                "rounded shadow-lg mb-4",
            ),
        )

        self.fields["lower_pace_range"].widget.attrs["@input.debounce"] = "input"
        self.fields["lower_pace_range"].widget.attrs[
            ":class"
        ] = "{'bg-red-200 dark:bg-red-200 text-red-800 dark:text-red-800': lower_pace_range.errorMessage}"

        self.fields["upper_pace_range"].widget.attrs["@input.debounce"] = "input"
        self.fields["upper_pace_range"].widget.attrs[
            ":class"
        ] = "{'bg-red-200 dark:bg-red-200 text-red-800 dark:text-red-800': upper_pace_range.errorMessage}"

    def fields_required(self, fields):
        for field in fields:
            if not self.cleaned_data.get(field, ""):
                msg = forms.ValidationError("This field is required.")
                self.add_error(field, msg)

    def get_classification_limit(self, club):
        surface_type = self.cleaned_data.get("surface_type")
        group_classification = self.cleaned_data.get("group_classification")
        classification_limit = apps.get_model("clubs.ClubRideClassificationLimit")
        return classification_limit.objects.filter(
            club=club,
            surface_type=surface_type,
            group_classification=group_classification,
        ).first()

    def clean(self):
        cleaned_data = super().clean()
        required_fields = []

        private = self.cleaned_data.get("privacy")
        club = self.cleaned_data.get("club")
        lower_pace_range = self.cleaned_data.get("lower_pace_range")
        upper_pace_range = self.cleaned_data.get("upper_pace_range")

        if private == EventMemberType.Members:
            required_fields.append("club")

        if len(required_fields) > 0:
            self.fields_required(required_fields)

        if club:
            classification_limit = self.get_classification_limit(club)
            if classification_limit and club.strict_ride_classification:
                limit = classification_limit
                lower = limit.lower_pace_range
                upper = limit.upper_pace_range

                event_lower = lower_pace_range
                event_upper = upper_pace_range

                if event_upper > upper:
                    self.add_error(
                        None,
                        f"The upper pace range must be less than or equal to {str(upper)}",
                    )

                if event_lower < lower:
                    self.add_error(
                        None,
                        f"The lower pace range must be greater than or equal to {str(lower)}",
                    )

        return cleaned_data

    class Meta:
        model = EventOccurence
        exclude = [
            "created_by",
            "event",
            "is_canceled",
            "slug",
            "modified_date",
            "modified_by",
        ]

        widgets = {
            "ride_date": forms.DateInput(
                format=("%Y-%m-%d"),
                attrs={
                    "class": "form-control",
                    "placeholder": "Select a date",
                    "type": "date",
                },
            ),
            "ride_time": forms.TimeInput(
                format="%H:%M",
                attrs={
                    "class": "form-control",
                    "placeholder": "Select a time",
                    "type": "time",
                },
            ),
        }

        field_classes = {"route": RouteChoiceField}

        help_texts = {
            "route": mark_safe("<a id='route_url_id' class='underline text-blue-700' href='' target='_blank'>Add</a>")
        }


class CreateEventForm(BaseEventForm):
    def __init__(self, user_clubs, user_routes, *args, **kwargs):
        super().__init__(*args, user_clubs=user_clubs, user_routes=user_routes, **kwargs)

        self.fields["frequency"].label = "Recurrence"
        self.helper.form_show_errors = False
        self.helper.layout = Layout(
            # Section 1
            Div(
                # Section Header
                self.section_header(self.general_header),
                # Section Body
                self.section_wrapper(
                    Field(
                        "name",
                        id="event_create_name",
                        css_class=self.css_class,
                        label_class=self.label_class,
                        wrapper_class="space-y-2",
                    ),
                    Field(
                        "description",
                        id="event_create_description",
                        css_class=self.css_class,
                        label_class=self.label_class,
                        wrapper_class="space-y-2",
                    ),
                    Field(
                        "privacy",
                        id="event_create_privacy",
                        css_class=self.css_class,
                        label_class=self.label_class,
                        wrapper_class="space-y-2",
                    ),
                    Field(
                        "club",
                        id="event_create_club",
                        css_class=self.css_class,
                        label_class=self.label_class,
                        wrapper_class="space-y-2",
                    ),
                    form_row(
                        Div(
                            HTML(
                                "<label for='routeChoiceButton' class='block text-gray-700 dark:text-gray-200 "
                                "text-sm font-bold'>Route<span class='asteriskField'>*</span></label>"
                            ),
                            StrictButton(
                                "Select Route",
                                css_id="routeChoiceButton",
                                css_class="w-full py-4 px-4 font-semibold btn-primary-color rounded-md shadow-lg",
                                **{"@click": "routeSelectModalOpen=true"},
                            ),
                            css_id="div_id_route_select",
                            css_class="col-span-12 space-y-2",
                        ),
                        padding_bottom="pb-2 mb-3",
                    ),
                    Field("route", type="hidden", id="route_id"),
                    Field(
                        "max_riders",
                        id="event_occurence_create_max_riders",
                        css_class=self.css_class,
                        label_class=self.label_class,
                        wrapper_class="space-y-2",
                    ),
                ),
                css_class="md:col-span-2 bg-white dark:bg-gray-900 rounded-lg "
                "overflow-hidden border border-gray-200 dark:border-gray-800 shadow-md",
            ),
            # Section 2
            Div(
                # Section Header
                self.section_header(self.ride_details_header),
                # Section Body
                self.section_wrapper(
                    Field(
                        "surface_type",
                        id="event_occurence_create_surface_type",
                        css_class=self.css_class,
                        label_class=self.label_class,
                        wrapper_class="space-y-2",
                    ),
                    Field(
                        "group_classification",
                        id="event_create_group_classification",
                        css_class=self.css_class,
                        label_class=self.label_class,
                        wrapper_class="space-y-2",
                    ),
                    Field(
                        "lower_pace_range",
                        id="event_create_lower_pace_range",
                        css_class=self.css_class,
                        label_class=self.label_class,
                        wrapper_class="space-y-2",
                    ),
                    HTML(
                        '<p x-show="lower_pace_range.errorMessage" x-text="lower_pace_range.errorMessage" '
                        ' class="-mt-4 mb-3 text-sm text-red-700 dark:text-red-400"></p>'
                    ),
                    Field(
                        "upper_pace_range",
                        id="event_create_upper_pace_range",
                        css_class=self.css_class,
                        label_class=self.label_class,
                        wrapper_class="space-y-2",
                    ),
                    HTML(
                        '<p x-show="upper_pace_range.errorMessage" x-text="upper_pace_range.errorMessage" '
                        ' class="-mt-4 mb-3 text-sm text-red-700 dark:text-red-400"></p>'
                    ),
                    Field(
                        "drop_designation",
                        id="event_create_drop_designation",
                        css_class=self.css_class,
                        label_class=self.label_class,
                        wrapper_class="space-y-2",
                    ),
                ),
                css_class="rounded-lg bg-card text-card-foreground shadow-sm border dark:border-slate-700",
            ),
            # Section 3
            Div(
                # Section Header
                self.section_header(self.schedule_header),
                # Section Body
                self.section_wrapper(
                    Field(
                        "start_date",
                        id="event_create_start_date",
                        css_class=self.css_class,
                        label_class=self.label_class,
                        wrapper_class="space-y-2",
                    ),
                    HTML(
                        '<p x-show="start_date.errorMessage" x-text="start_date.errorMessage" '
                        ' class="-mt-4 mb-3 text-sm text-red-700 dark:text-red-400"></p>'
                    ),
                    Field(
                        "end_date",
                        id="event_create_end_date",
                        css_class=self.css_class,
                        label_class=self.label_class,
                        wrapper_class="space-y-2",
                    ),
                    HTML(
                        '<p x-show="end_date.errorMessage" x-text="end_date.errorMessage" '
                        ' class="-mt-4 mb-3 text-sm text-red-700 dark:text-red-400"></p>'
                    ),
                    Field(
                        "time_zone",
                        id="event_create_time_zone",
                        css_class=self.css_class,
                        label_class=self.label_class,
                        wrapper_class="space-y-2",
                    ),
                    Field(
                        "ride_time",
                        id="event_create_ride_time",
                        css_class=self.css_class,
                        label_class=self.label_class,
                        wrapper_class="space-y-2",
                    ),
                    Field(
                        "frequency",
                        id="event_create_frequency",
                        css_class=self.css_class,
                        label_class=self.label_class,
                        wrapper_class="space-y-2",
                    ),
                    InlineCheckboxes("weekdays", label="", wrapper_class="mb-3 space-y-2"),
                ),
                css_class="rounded-lg bg-card text-card-foreground shadow-sm border dark:border-slate-700",
            ),
        )

        self.fields["weekdays"].label = ""
        self.fields["lower_pace_range"].widget.attrs["@input.debounce"] = "input"
        self.fields["lower_pace_range"].widget.attrs[
            ":class"
        ] = "{'bg-red-200 dark:bg-red-200 text-red-800 dark:text-red-800': lower_pace_range.errorMessage}"

        self.fields["upper_pace_range"].widget.attrs["@input.debounce"] = "input"
        self.fields["upper_pace_range"].widget.attrs[
            ":class"
        ] = "{'bg-red-200 dark:bg-red-200 text-red-800 dark:text-red-800': upper_pace_range.errorMessage}"

        self.fields["start_date"].widget.attrs["@change.debounce"] = "change"
        self.fields["start_date"].widget.attrs[
            ":class"
        ] = "{'bg-red-200 dark:bg-red-200 text-red-800 dark:text-red-800': start_date.errorMessage}"

        self.fields["end_date"].widget.attrs["@change.debounce"] = "change"
        self.fields["end_date"].widget.attrs[
            ":class"
        ] = "{'bg-red-200 dark:bg-red-200 text-red-800 dark:text-red-800': end_date.errorMessage}"

    def fields_required(self, fields):
        for field in fields:
            if not self.cleaned_data.get(field, ""):
                msg = forms.ValidationError("This field is required.")
                self.add_error(field, msg)

    def get_classification_limit(self, club):
        surface_type = self.cleaned_data.get("surface_type")
        group_classification = self.cleaned_data.get("group_classification")
        classification_limit = apps.get_model("clubs.ClubRideClassificationLimit")
        return classification_limit.objects.filter(
            club=club,
            surface_type=surface_type,
            group_classification=group_classification,
        ).first()

    def clean(self):
        cleaned_data = super().clean()
        required_fields = []

        private = self.cleaned_data.get("privacy")
        frequency = self.cleaned_data.get("frequency")
        club = self.cleaned_data.get("club")
        lower_pace_range = self.cleaned_data.get("lower_pace_range")
        upper_pace_range = self.cleaned_data.get("upper_pace_range")
        start_date = self.cleaned_data.get("start_date")
        end_date = self.cleaned_data.get("end_date")

        if private == EventMemberType.Members:
            required_fields.append("club")

        if frequency == RecurrenceFrequency.Weekly:
            required_fields.append("weekdays")

        if len(required_fields) > 0:
            self.fields_required(required_fields)

        if club:
            classification_limit = self.get_classification_limit(club)
            if classification_limit and club.strict_ride_classification:
                limit = classification_limit
                lower = limit.lower_pace_range
                upper = limit.upper_pace_range

                event_lower = lower_pace_range
                event_upper = upper_pace_range

                if event_upper > upper:
                    self.add_error(
                        None,
                        f"The upper pace range must be less than or equal to {str(upper)}",
                    )

                if event_lower < lower:
                    self.add_error(
                        None,
                        f"The lower pace range must be greater than or equal to {str(lower)}",
                    )

        if end_date > start_date + relativedelta(days=+366):
            self.add_error("end_date", "End date must be within 1 year of start date")

        return cleaned_data

    class Meta:
        model = Event
        exclude = ["created_by"]

        widgets = {
            "start_date": forms.DateInput(
                format="%-m/%-d/%Y",
                attrs={
                    "class": "form-control",
                    "placeholder": "Select a date",
                    "type": "date",
                },
            ),
            "end_date": forms.DateInput(
                format="%-m/%-d/%Y",
                attrs={
                    "class": "form-control",
                    "placeholder": "Select a date",
                    "type": "date",
                },
            ),
            "ride_time": forms.TimeInput(
                format="%-I:%M %p",
                attrs={
                    "class": "form-control",
                    "placeholder": "Select a time",
                    "type": "time",
                },
            ),
        }

        field_classes = {"route": RouteChoiceField}

        help_texts = {
            "route": mark_safe("<a id='route_url_id' class='underline text-blue-700' href='' target='_blank'>Add</a>")
        }
