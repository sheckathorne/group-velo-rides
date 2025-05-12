from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, Fieldset, Layout
from django import forms

from group_velo.clubs.fields import LeftSideCheckboxInput
from group_velo.routes.models import Route
from group_velo.utils.utils import css_container


class RouteForm(forms.ModelForm):
    def __init__(self, user_clubs, *args, **kwargs):
        fieldset_class = "w-full h-auto p-2 mb-3 space-y-2"
        css_class = "w-full shadow-lg"
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.css_container = css_container()
        self.helper.label_class = "block text-gray-700 text-sm font-bold dark:text-gray-100"
        self.helper.form_tag = False
        self.fields["club"].choices = user_clubs
        self.helper.layout = Layout(
            Div(
                Fieldset(
                    "Route Info",
                    Field("name", css_clss=css_class),
                    Field("url", css_clss=css_class),
                    css_class=fieldset_class,
                ),
                Fieldset(
                    "Distance / Elevation",
                    Field("distance", css_class=css_class),
                    Field("elevation", css_class=css_class),
                    css_class=fieldset_class,
                ),
                css_class="w-full grid xl:grid-cols-3 md:grid-cols-2 grid-cols-1",
            ),
            Div(
                Fieldset(
                    "Start Address",
                    Field("start_location_name", css_class=css_class),
                    Field("start_address", css_class=css_class),
                    Field("start_city", css_class=css_class),
                    Field("start_state", css_class=css_class),
                    Field("start_zip_code", css_class=css_class),
                    css_class=fieldset_class,
                ),
                css_class="w-full grid xl:grid-cols-3 md:grid-cols-2 grid-cols-1",
            ),
            Div(
                Fieldset(
                    "Sharing",
                    Div(
                        Field(
                            "shared",
                            template="tailwind/checkbox_left.html",
                            css_class="rounded mr-4",
                            wrapper_class="xl:mb-1 w-full",
                        ),
                        id="route_create_shared_row",
                    ),
                    Field("club", css_class=css_class),
                    css_class=fieldset_class,
                ),
                css_class="w-full grid xl:grid-cols-3 md:grid-cols-2 grid-cols-1",
            ),
        )

    def fields_required(self, fields):
        for field in fields:
            if not self.cleaned_data.get(field, ""):
                msg = forms.ValidationError("This field is required.")
                self.add_error(field, msg)

    def clean(self):
        private = self.cleaned_data.get("shared")
        if private:
            self.fields_required(["club"])
        return self.cleaned_data

    class Meta:
        model = Route
        exclude = ["created_by", "date_created"]

        widgets = {
            "shared": LeftSideCheckboxInput(),
        }
