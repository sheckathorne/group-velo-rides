from crispy_forms.layout import HTML, Div
from django import forms


class BaseForm(forms.ModelForm):
    def section_wrapper(self, *args):
        return Div(
            Div(
                *args,
                css_class="space-y-2",
            ),
            css_class="p-6 pt-6 space-y-4",
        )

    def section_header(self, section_data):
        colors = section_data["colors"]
        header_svg = section_data["header_svg"]
        header_title = section_data["header_title"]
        header_subtitle = section_data["header_subtitle"]

        self.prefix_class = (
            "w-full px-4 shadow-lg focus:ring-2 dark:bg-gray-800 dark:text-gray-200 text-gray-700 "
            "focus:ring-blue-700 dark:border-gray-700 border-gray-300 border shadow rounded-r-md "
            "dark:focus:ring-blue-500 px-4 leading-normal py-2 appearance-none bg-white rounded-l-none"
        )

        self.css_class = (
            "w-full shadow-lg rounded-md focus:ring-2 dark:bg-gray-800 dark:text-gray-200 text-gray-700 "
            "focus:ring-blue-700 dark:border-gray-700 border-gray-300 border shadow rounded dark:focus:ring-blue-500 "
            "px-4 leading-normal py-2 appearance-none bg-white"
        )

        self.label_class = "text-sm leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 font-medium"
        self.checkbox_template = "tailwind/checkbox_left.html"

        header_css_class = (
            f"flex flex-col space-y-1.5 p-6 bg-gradient-to-r {colors['light']['from']} "
            f"{colors['light']['to']} {colors['dark']['from']} "
            f"{colors['dark']['to']} text-white rounded-t-lg"
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
