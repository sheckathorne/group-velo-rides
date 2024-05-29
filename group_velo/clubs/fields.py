from django.forms.widgets import CheckboxInput


class LeftSideCheckboxInput(CheckboxInput):
    template_name = "tailwind/checkbox_input_box.html"
