import datetime

import pytz
from crispy_forms.bootstrap import StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Div, Field, Fieldset, Layout
from django import forms
from django.core.exceptions import ValidationError
from django.forms.widgets import RadioSelect
from django.template.loader import render_to_string
from image_uploader_widget.widgets import ImageUploaderWidget

from group_velo.clubs.fields import LeftSideCheckboxInput
from group_velo.clubs.models import (
    Club,
    ClubMembership,
    ClubMembershipRequest,
    ClubRideClassificationLimit,
    ClubVerificationRequest,
)
from group_velo.data.choices import MemberType, RequestStatus
from group_velo.utils.utils import base_input_style, css_container, dropdown, form_row, form_row_new


class ClubForm(forms.ModelForm):
    class Meta:
        model = Club
        fields = [
            "name",
            "abbreviation",
            "description",
            "url",
            "logo",
            "city",
            "state",
            "zip_code",
            "email_address",
            "phone_number",
            "private",
            "privacy_level",
            "active",
            "private_ride_attendence",
            "private_ride_waitlist",
            "allow_ride_discussion",
            "strict_ride_classification",
        ]

        widgets = {
            "logo": ImageUploaderWidget(),
            "active": LeftSideCheckboxInput(),
            "private": LeftSideCheckboxInput(),
            "privacy_level": RadioSelect(),
            "private_ride_attendence": LeftSideCheckboxInput(),
            "private_ride_waitlist": LeftSideCheckboxInput(),
            "allow_ride_discussion": LeftSideCheckboxInput(),
            "strict_ride_classification": LeftSideCheckboxInput(),
        }

    def __init__(self, *args, **kwargs):
        fieldset_class = "w-full h-auto p-2 mb-3 space-y-2"
        css_class = "w-full shadow-lg"
        checkbox_template = "tailwind/checkbox_left.html"
        self.submit_text = kwargs.pop("submit_text", "Submit")

        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.css_container = css_container()
        self.helper.label_class = "block text-gray-700 text-sm font-bold dark:text-gray-100"
        self.helper.form_tag = False

        self.helper.layout = Layout(
            Div(
                HTML(
                    '<h1 class="text-3xl font-bold tracking-tight">Edit Club</h1>'
                    '<p class="text-muted-foreground">Update your club'
                    "s information and settings</p>"
                ),
                css_class="flex flex-col gap-2",
            )
        )

        self.helper.layout = Layout(
            Div(
                Fieldset(
                    "General",
                    Field("name", css_class=css_class),
                    Field("abbreviation", css_class=css_class),
                    Field("description", css_class=css_class),
                    Field("url", css_class=css_class),
                    Field("logo", css_class=css_class),
                    css_class=fieldset_class,
                ),
                Fieldset(
                    "Location/Contact",
                    Field("city", css_class=css_class),
                    Field("state", css_class=css_class),
                    Field("zip_code", css_class=css_class),
                    Field("email_address", css_class=css_class),
                    Field(
                        "phone_number",
                        id="club_create_phone_number",
                        css_class=base_input_style(),
                        label_class="dark:text-gray-200",
                        x_mask="(999) 999-9999",
                    ),
                    css_class=fieldset_class,
                ),
                Fieldset(
                    "Settings",
                    Div(
                        Field("privacy_level", wrapper_class="xl:mb-1 w-full"),
                        id="privacy_level_row",
                        css_class="py-2",
                    ),
                    Div(
                        Field(
                            "active",
                            template=checkbox_template,
                            wrapper_class="xl:mb-1 w-full",
                        ),
                        id="active_check_row",
                        css_class="py-2",
                    ),
                    Div(
                        Field(
                            "private_ride_attendence",
                            template=checkbox_template,
                            wrapper_class="xl:mb-1  w-full",
                        ),
                        id="private_attendence_row",
                        css_class="py-2",
                    ),
                    Div(
                        Field(
                            "private_ride_waitlist",
                            template=checkbox_template,
                            wrapper_class="xl:mb-1  w-full",
                        ),
                        id="private_waitlist_row",
                        css_class="py-2",
                    ),
                    Div(
                        Field(
                            "allow_ride_discussion",
                            template=checkbox_template,
                            wrapper_class="xl:mb-1  w-full",
                        ),
                        id="allow_ride_discussion_row",
                        css_class="py-2",
                    ),
                    Div(
                        Field(
                            "strict_ride_classification",
                            x_model="showStrictRideClassBtn",
                            template=checkbox_template,
                            wrapper_class="xl:mb-1  w-full",
                        ),
                        id="strict_ride_classification_row",
                        css_class="py-2",
                    ),
                    css_class=fieldset_class,
                ),
                css_class="w-full grid xl:grid-cols-3 md:grid-cols-2 grid-cols-1",
            ),
        )

        info_icon = (
            "<button x-tooltip.placement.auto-start='{ content: () => $refs.privacyPopoverTemplate.innerHTML, "
            "allowHTML: true, appendTo: $root }' type='button'><i class='fa-solid fa-circle-info'></i></button>"
        )

        privacy_level_label = (
            "" if self.fields["privacy_level"].label is None else self.fields["privacy_level"].label + " "
        )

        self.fields["privacy_level"].label = privacy_level_label + info_icon


class ClubSearchForm(forms.Form):
    club_name = forms.CharField(
        label="club name",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Club Name"}),
    )

    zip_code = forms.CharField(
        label="zip code",
        max_length=5,
        min_length=5,
        required=False,
        widget=forms.NumberInput(attrs={"placeholder": "Near Zip Code"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        club_fade_id = "club_fade"
        zip_fade_id = "zip_fade"

        self.helper = FormHelper(self)
        self.fields["zip_code"].label = ""
        self.fields["club_name"].label = ""
        self.helper.layout = Layout(
            HTML(
                '<div class="grid md:grid-cols-12 gap-2 mb-4">'
                '<div class="lg:col-span-3 col-span-12">'
                '<div class="bg-transparent">'
                '<label for="club_name_text" class="sr-only">Search Club Name</label>'
                '<div class="relative mt-1">'
            ),
            HTML(render_to_string("icons/magnifying_glass.html")),
            HTML(render_to_string("animations/request_spinner.html", {"id": club_fade_id, "position": "left"})),
            Field(
                "club_name",
                id="club_name_text",
                hx_post="",
                hx_trigger="input changed delay:500ms, search",
                hx_target="#response-alert",
                hx_swap="outerHTML",
                hx_vals='{ "autoSubmit": true }',
                hx_indicator=f".{club_fade_id}",
                css_class="w-full p-2 pl-10 text-sm text-gray-900 border "
                "border-gray-300 rounded-lg bg-gray-50 dark:bg-gray-700 dark:border-gray-500 dark:text-gray-200 "
                "focus:ring-blue-500 focus:border-blue-500 shadow-lg",
                attrs={"placeholder": "Search Club Name"},
            ),
            HTML(
                "</div>"
                "</div>"
                "</div>"
                '<div class="lg:col-span-3 col-span-12">'
                '<div class="bg-transparent">'
                '<label for="zip_code_text" class="sr-only">Near Zip Code</label>'
                '<div class="relative mt-1">'
            ),
            HTML(render_to_string("icons/magnifying_glass.html")),
            HTML(render_to_string("animations/request_spinner.html", {"id": zip_fade_id, "position": "left"})),
            Field(
                "zip_code",
                id="zip_code_text",
                hx_post="",
                hx_trigger="input changed delay:500ms, search",
                hx_indicator=f".{zip_fade_id}",
                hx_target="#response-alert",
                hx_swap="outerHTML",
                hx_vals='{ "autoSubmit": true }',
                css_class="w-full p-2 pl-10 text-sm text-gray-900 border "
                "border-gray-300 rounded-lg bg-gray-50 dark:bg-gray-700 dark:border-gray-500 dark:text-gray-200 "
                "focus:ring-blue-500 focus:border-blue-500 shadow-lg",
            ),
            HTML("</div></div></div><div class='lg:col-span-3 col-span-12'><div class='relative mt-1'>"),
            StrictButton(
                "Search",
                value="Search",
                type="button",
                hx_post="",
                hx_trigger="click",
                hx_target="#response-alert",
                hx_swap="outerHTML",
                css_class="w-full p-2 btn-primary-color rounded-lg shadow-lg font-medium text-sm",
            ),
            HTML("</div></div></div>"),
        )

    def clean(self):
        club_name = self.cleaned_data.get("club_name")
        zip_code = self.cleaned_data.get("zip_code")

        if not club_name and not zip_code:
            raise ValidationError("Enter either a club name or zip code to search.")


class ClubMembershipForm(forms.ModelForm):
    class Meta:
        model = ClubMembership
        fields = ["membership_expires", "active", "membership_type"]

        widgets = {"membership_expires": forms.DateInput(attrs={"class": "form-control", "type": "date"})}

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        self.slug = kwargs.pop("slug", None)
        self.membership_request_id = kwargs.pop("membership_request_id", None)
        member = kwargs.get("instance", None)
        member_dropdown_disabled = False

        if member:
            member_dropdown_disabled = member.membership_type == MemberType(MemberType.Creator).value

        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.css_container = css_container()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            form_row(
                dropdown("membership_type", "member", width="col-span-12"),
                padding_bottom="pb-4",
            ),
            form_row(
                Div(
                    Field("membership_expires", id="member_create_membership_expires"),
                    css_class="md:col-span-12",
                ),
                padding_bottom="pb-4",
            ),
            form_row(
                Div(
                    Field(
                        "active",
                        wrapper_class="flex flex-row items-center",
                        css_class="ml-4 rounded",
                    ),
                    css_class="col-span-12 mb-1",
                ),
                padding_bottom="pb-4",
            ),
            Div(
                StrictButton(
                    "Confirm",
                    value="Confirm",
                    type="submit",
                    css_class="inline-block btn-primary-color w-full",
                ),
                css_class="modal-footer",
            ),
        )

        info_icon = (
            "<button x-tooltip.placement.right='{ content: () => $refs.membershipPopoverTemplate.innerHTML, "
            "allowHTML: true, appendTo: $root }' type='button'><i class='fa-solid fa-circle-info'></i></button>"
        )

        membership_type_label = self.fields["membership_type"].label + " "

        self.fields["membership_type"].label = membership_type_label + info_icon
        self.fields["membership_type"].disabled = member_dropdown_disabled
        self.fields["membership_expires"].disabled = member_dropdown_disabled
        self.fields["active"].disabled = member_dropdown_disabled

        # When approving join request, set initial values in form.
        if self.membership_request_id:
            self.fields["membership_type"].initial = MemberType.PaidMember
            self.fields["membership_expires"].initial = datetime.date.today() + datetime.timedelta(weeks=52)
            self.fields["active"].initial = True

    def clean(self):
        requestor_membership = ClubMembership.objects.get(user=self.user, club__slug=self.slug)
        requestor_role = requestor_membership.membership_type
        new_role_type = self.cleaned_data["membership_type"]
        creator_role_type = MemberType(MemberType.Creator).value

        # When approving join request, set the approver details when the form is submitted
        if self.membership_request_id:
            tz = pytz.timezone("America/Chicago")
            membership_request = ClubMembershipRequest.objects.get(pk=self.membership_request_id)
            membership_request.status = RequestStatus.Approved
            membership_request.responder = self.user
            membership_request.response_date = datetime.datetime.now(tz)
            membership_request.save()

        if new_role_type == creator_role_type and requestor_role > creator_role_type:
            raise ValidationError("Only creators can promote others to the 'creator' role.")


class ClubRideClassificationLimitForm(forms.ModelForm):
    class Meta:
        model = ClubRideClassificationLimit
        fields = [
            "club",
            "surface_type",
            "group_classification",
            "lower_pace_range",
            "upper_pace_range",
            "active",
        ]

    def __init__(
        self,
        *args,
        club_id=None,
        surface_type=("R", "Road"),
        group_classification=("A", "A"),
        club_slug=None,
        first_row=False,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.css_container = css_container()
        self.helper.form_tag = False
        self.fields["lower_pace_range"].required = False
        self.fields["upper_pace_range"].required = False

        self.label = (
            (
                '<label for="group_classification" class="block text-sm '
                'font-bold text-gray-800 dark:text-gray-100">Ride Classification</label>'
            )
            if first_row
            else ""
        )

        self.group_class_field = HTML(
            '<div class="w-auto" id="generic-row">'
            f"{self.label}"
            '<span class="w-full block appearance-none text-gray-800 text-center dark:text-gray-300 py-2" '
            f'id="group_classification">{group_classification[1]}</span> '
            "</div>"
        )

        self.prefix = f"{surface_type[0]}_{group_classification[0]}"

        self.form_fields = [
            Field("club", type="hidden", value=club_id),
            Field("surface_type", type="hidden", value=surface_type[0]),
            Field("group_classification", type="hidden", value=group_classification[0]),
            Field("active", type="hidden", value=True),
            Div(
                Field(
                    "lower_pace_range",
                    css_class="num-only lower-pace-range-field",
                    data_rules='["numeric", "lowerLessThanUpper:999"]',
                    short_name=f"{self.prefix}_lpr",
                ),
                HTML(
                    f'<p x-show="{self.prefix}_lpr.errorMessage" x-text="{self.prefix}_lpr.errorMessage" '
                    'class="mt-1 mb-2 text-sm text-red-700 dark:text-red-400"></p>'
                ),
            ),
            Div(
                Field(
                    "upper_pace_range",
                    css_class="num-only upper-pace-range-field",
                    data_rules='["numeric","upperGreaterThanLower:-1"]',
                    short_name=f"{self.prefix}_upr",
                ),
                HTML(
                    f'<p x-show="{self.prefix}_upr.errorMessage" x-text="{self.prefix}_upr.errorMessage" '
                    'class="mt-1 mb-2 text-sm text-red-700 dark:text-red-400"></p>'
                ),
            ),
        ]

        if not first_row:
            self.helper.form_show_labels = False

        self.helper.layout = Layout(
            form_row_new(
                Div(
                    self.group_class_field,
                    *self.form_fields,
                    css_class="grid gap-2 grid-cols-[130px_minmax(0,1fr)_minmax(0,1fr)] pb-2 w-full xl:w-2/3",
                ),
            ),
        )

        error_class = "!bg-red-200 !dark:bg-red-200 !text-red-800 !dark:text-red-800 !focus:ring-red-700"
        error_class_lpr = f"{{ '{error_class}': {self.prefix}_lpr.errorMessage }}"
        error_class_upr = f"{{ '{error_class}': {self.prefix}_upr.errorMessage }}"

        self.fields["lower_pace_range"].widget.attrs["@input.debounce"] = "input"
        self.fields["lower_pace_range"].widget.attrs[":class"] = error_class_lpr

        self.fields["upper_pace_range"].widget.attrs["@input.debounce"] = "input"
        self.fields["upper_pace_range"].widget.attrs[":class"] = error_class_upr

    def clean(self):
        super().clean()
        cleaned_data = self.cleaned_data
        lower_pace_range = cleaned_data.get("lower_pace_range", None)
        upper_pace_range = cleaned_data.get("upper_pace_range", None)
        pace_ranges = [upper_pace_range, lower_pace_range]

        if any(pace_ranges) and not all(pace_ranges):
            if not lower_pace_range:
                self.add_error("lower_pace_range", "Must enter both pace ranges")
            else:
                self.add_error("upper_pace_range", "Must enter both pace ranges")

        if all(pace_ranges):
            if lower_pace_range >= upper_pace_range:
                self.add_error("lower_pace_range", "Lower pace range must be less than upper.")

            if upper_pace_range <= lower_pace_range:
                self.add_error("upper_pace_range", "Upper pace range must be greater than lower.")

        return cleaned_data


class ClubVerificationRequestForm(forms.ModelForm):
    class Meta:
        model = ClubVerificationRequest
        fields = ["contact_email"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.css_container = css_container()
        self.helper.form_tag = False
        self.helper.layout = Layout(Div(Field("contact_email"), css_class="m-4"))
