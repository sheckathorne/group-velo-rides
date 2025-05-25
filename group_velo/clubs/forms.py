import datetime

import pytz
from crispy_forms.bootstrap import StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Div, Field, Layout
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
from group_velo.utils.layout import IconPrefixedField
from group_velo.utils.utils import css_container, dropdown, form_row, get_group_classification_color


class BaseClubForm(forms.ModelForm):
    def section_header(self, section_data):
        colors = section_data["colors"]
        header_svg = section_data["header_svg"]
        header_title = section_data["header_title"]
        header_subtitle = section_data["header_subtitle"]

        header_css_class = (
            f"flex flex-col space-y-1.5 p-6 bg-gradient-to-r from-{colors['light']['from']} "
            f"to-{colors['light']['to']} dark:from-{colors['dark']['from']} "
            f"dark:to-{colors['dark']['to']} text-white rounded-t-lg"
        )

        return Div(
            Div(
                HTML(header_svg),
                HTML("<h3 class='text-2xl font-semibold leading-none " f"tracking-tight'>{header_title}</h3>"),
                css_class="flex items-center gap-2",
            ),
            HTML(f"<p class='text-sm text-white/80'>{header_subtitle}</p>"),
            css_class=header_css_class,
        )


class ClubForm(BaseClubForm):
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
        prefix_class = (
            "w-full px-4 shadow-lg focus:ring-2 dark:bg-gray-800 dark:text-gray-200 text-gray-700 "
            "focus:ring-blue-700 dark:border-gray-700 border-gray-300 border shadow rounded-r-md "
            "dark:focus:ring-blue-500 px-4 leading-normal py-2 appearance-none bg-white rounded-l-none"
        )

        css_class = (
            "w-full shadow-lg rounded-md focus:ring-2 dark:bg-gray-800 dark:text-gray-200 text-gray-700 "
            "focus:ring-blue-700 dark:border-gray-700 border-gray-300 border shadow rounded dark:focus:ring-blue-500 "
            "px-4 leading-normal py-2 appearance-none bg-white"
        )

        label_class = "text-sm leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 font-medium"
        checkbox_template = "tailwind/checkbox_left.html"
        self.submit_text = kwargs.pop("submit_text", "Submit")

        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.css_container = css_container()
        self.helper.label_class = "block text-gray-700 text-sm font-bold dark:text-gray-100"
        self.helper.form_tag = False

        general_header = {
            "header_svg": (
                "<svg xmlns='http://www.w3.org/2000/svg' width='24' height='24' "
                "viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' "
                "stroke-linecap='round' stroke-linejoin='round' class='lucide lucide-building2 "
                "h-5 w-5'><path d='M6 22V4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v18Z'></path>"
                "<path d='M6 12H4a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h2'>"
                "</path><path d='M18 9h2a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-2'></path>"
                "<path d='M10 6h4'></path><path d='M10 10h4'>"
                "</path><path d='M10 14h4'></path><path d='M10 18h4'></path></svg>"
            ),
            "header_title": "General Information",
            "header_subtitle": "Basic details about your club",
            "colors": {
                "light": {"from": "violet-500", "to": "purple-600"},
                "dark": {"from": "violet-600", "to": "purple-800"},
            },
        }

        contact_header = {
            "header_svg": (
                '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" '
                'viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
                'stroke-linecap="round" stroke-linejoin="round" class="lucide '
                'lucide-map-pin h-5 w-5"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z">'
                '</path><circle cx="12" cy="10" r="3"></circle></svg>'
            ),
            "header_title": "Location & Contact",
            "header_subtitle": "Where your club is located and how to reach you",
            "colors": {"light": {"from": "sky-500", "to": "blue-600"}, "dark": {"from": "sky-600", "to": "blue-800"}},
        }

        settings_header = {
            "header_svg": (
                '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" '
                'viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
                'stroke-linecap="round" stroke-linejoin="round" class="lucide '
                'lucide-shield h-5 w-5">'
                '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 '
                "13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 "
                '3.81 17 5 19 5a1 1 0 0 1 1 1z"></path></svg>'
            ),
            "header_title": "Club Settings",
            "header_subtitle": "Configure privacy and behavior settings for your club",
            "colors": {
                "light": {"from": "amber-500", "to": "orange-600"},
                "dark": {"from": "amber-600", "to": "orange-800"},
            },
        }

        self.helper.layout = Layout(
            # Section 1
            Div(
                # Section Header
                self.section_header(general_header),
                # Section Body
                Div(
                    Div(
                        Field("name", css_class=css_class, label_class=label_class, wrapper_class="space-y-2"),
                        Field(
                            "abbreviation",
                            css_class=css_class,
                            label_class=label_class,
                            wrapper_class="space-y-2",
                        ),
                        Field(
                            "description",
                            css_class=css_class,
                            label_class=label_class,
                            wrapper_class="space-y-2",
                        ),
                        IconPrefixedField(
                            "url",
                            template="tailwind/layout/icon_prefixed_field.html",
                            icon_path="icons/url.html",
                            css_class=prefix_class,
                        ),
                        Field("logo", css_class=css_class, label_class=label_class, wrapper_class="space-y-2"),
                        css_class="space-y-2",
                    ),
                    css_class="p-6 pt-6 space-y-4",
                ),
                css_class="rounded-lg bg-card text-card-foreground shadow-sm border dark:border-slate-700",
            ),
            # Section 2
            Div(
                # Section Header
                self.section_header(contact_header),
                # Section Body
                Div(
                    Div(
                        Field("city", css_class=css_class, label_class=label_class, wrapper_class="space-y-2"),
                        Field("state", css_class=css_class, label_class=label_class, wrapper_class="space-y-2"),
                        Field("zip_code", css_class=css_class, label_class=label_class, wrapper_class="space-y-2"),
                        IconPrefixedField(
                            "email_address",
                            template="tailwind/layout/icon_prefixed_field.html",
                            icon_path="icons/email.html",
                            css_class=prefix_class,
                        ),
                        IconPrefixedField(
                            "phone_number",
                            template="tailwind/layout/icon_prefixed_field.html",
                            icon_path="icons/phone.html",
                            id="club_create_phone_number",
                            x_mask="(999) 999-9999",
                            css_class=prefix_class,
                        ),
                        css_class="space-y-2",
                    ),
                    css_class="p-6 pt-6 space-y-4",
                ),
                css_class="rounded-lg bg-card text-card-foreground shadow-sm border dark:border-slate-700",
            ),
            # Section 3
            Div(
                # Section Header
                self.section_header(settings_header),
                # Section Body
                Div(
                    Div(
                        Div(
                            Div(
                                Div(
                                    Field(
                                        "privacy_level",
                                        wrapper_class="space-y-2",
                                    ),
                                    id="privacy_level_row",
                                ),
                                css_class="space-y-2",
                            ),
                            HTML('<hr class="border-gray-200 dark:border-gray-700">'),
                            Div(
                                Field(
                                    "active",
                                    template=checkbox_template,
                                    wrapper_class="xl:mb-1 w-full",
                                ),
                                id="active_check_row",
                                css_class="py-2",
                            ),
                            css_class="space-y-4",
                        ),
                        Div(
                            Div(
                                Field(
                                    "private_ride_attendence",
                                    template=checkbox_template,
                                    wrapper_class="xl:mb-1 w-full",
                                ),
                                id="private_attendence_row",
                                css_class="py-2",
                            ),
                            Div(
                                Field(
                                    "private_ride_waitlist",
                                    template=checkbox_template,
                                    wrapper_class="xl:mb-1 w-full",
                                ),
                                id="private_waitlist_row",
                                css_class="py-2",
                            ),
                            Div(
                                Field(
                                    "allow_ride_discussion",
                                    template=checkbox_template,
                                    wrapper_class="xl:mb-1 w-full",
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
                            css_class="space-y-4",
                        ),
                        css_class="grid gap-6 md:grid-cols-2",
                    ),
                    css_class="p-6",
                ),
                css_class="md:col-span-2 bg-white dark:bg-gray-900 rounded-lg "
                "overflow-hidden border border-gray-200 dark:border-gray-800 shadow-md",
            ),
        )

        info_icon = (
            "<div "
            'class="relative group cursor-help" '
            'x-tooltip.placement.auto-start="{ '
            "content: () => $refs.privacyPopoverTemplate.innerHTML, "
            "allowHTML: true, appendTo: $root "
            '}"'
            ">"
            '<div class="cursor-help text-gray-500 dark:text-gray-400">'
            '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" '
            'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            '<circle cx="12" cy="12" r="10"></circle>'
            '<path d="M12 16v-4"></path>'
            '<path d="M12 8h.01"></path>'
            "</svg>"
            "</div>"
            "</div>"
        )

        privacy_level_label = (
            "" if self.fields["privacy_level"].label is None else self.fields["privacy_level"].label + " "
        )

        self.fields["privacy_level"].label = (
            "<div class='flex items-center gap-2'>"
            + privacy_level_label
            + info_icon
            + "<span class='speicalAsteriskField'>*</span></div>"
        )
        self.fields["privacy_level"].label


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

        classification_label, classification_display = group_classification
        surface_type_label, _ = surface_type

        label_color = get_group_classification_color(classification_label)
        tooltip = (
            f' x-tooltip.raw="{classification_display}" class="cursor-help"'
            if classification_label != classification_display
            else ""
        )

        self.group_class_field = HTML(
            f"<div{tooltip}>"
            '<div class="py-5 flex items-center justify-center">'
            '<span class="inline-flex '
            f"items-center justify-center h-8 w-8 rounded-full {label_color} "
            f'font-semibold">{classification_label}</span></div>'
            "</div>"
        )

        self.prefix = f"{surface_type_label}_{classification_label}"

        self.form_fields = [
            Field("club", type="hidden", value=club_id),
            Field("surface_type", type="hidden", value=surface_type_label),
            Field("group_classification", type="hidden", value=classification_label),
            Field("active", type="hidden", value=True),
            Div(
                Field(
                    "lower_pace_range",
                    css_class="num-only lower-pace-range-field my-4",
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
                    css_class="num-only upper-pace-range-field my-4",
                    data_rules='["numeric","upperGreaterThanLower:-1"]',
                    short_name=f"{self.prefix}_upr",
                ),
                HTML(
                    f'<p x-show="{self.prefix}_upr.errorMessage" x-text="{self.prefix}_upr.errorMessage" '
                    'class="mt-1 mb-2 text-sm text-red-700 dark:text-red-400"></p>'
                ),
            ),
        ]

        self.helper.form_show_labels = False

        self.helper.layout = Layout(
            Div(
                self.group_class_field,
                *self.form_fields,
                css_class=(
                    "grid grid-cols-[1fr_1fr_1fr] border-b border-gray-200 dark:border-gray-700 "
                    "hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors duration-150 gap-4"
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
