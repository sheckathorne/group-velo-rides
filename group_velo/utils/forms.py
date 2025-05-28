from crispy_forms.layout import HTML, Div
from django import forms


class BaseForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.submit_text = kwargs.pop("submit_text", "Submit")

        super().__init__(*args, **kwargs)

        self.svgs = {
            "general": (
                "<svg xmlns='http://www.w3.org/2000/svg' width='24' height='24' "
                "viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' "
                "stroke-linecap='round' stroke-linejoin='round' class='lucide lucide-building2 "
                "h-5 w-5'><path d='M6 22V4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v18Z'></path>"
                "<path d='M6 12H4a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h2'>"
                "</path><path d='M18 9h2a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-2'></path>"
                "<path d='M10 6h4'></path><path d='M10 10h4'>"
                "</path><path d='M10 14h4'></path><path d='M10 18h4'></path></svg>"
            ),
            "location": (
                '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" '
                'viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
                'stroke-linecap="round" stroke-linejoin="round" class="lucide '
                'lucide-map-pin h-5 w-5"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z">'
                '</path><circle cx="12" cy="10" r="3"></circle></svg>'
            ),
            "settings": (
                '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" '
                'viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
                'stroke-linecap="round" stroke-linejoin="round" class="lucide '
                'lucide-shield h-5 w-5">'
                '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 '
                "13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 "
                '3.81 17 5 19 5a1 1 0 0 1 1 1z"></path></svg>'
            ),
            "classification": (
                '<svg class="lucide lucide-shield h-5 w-5" '
                'xmlns="http://www.w3.org/2000/svg" '
                'stroke="currentColor" '
                'shape-rendering="geometricPrecision" '
                'text-rendering="geometricPrecision" '
                'image-rendering="optimizeQuality" '
                'fill-rule="evenodd" '
                'clip-rule="evenodd" '
                'viewBox="0 0 512 479.263"> '
                '<path fill="currentColor" fill-rule="nonzero" d="M383.448 28.962v140.557c0 7.973-3.257 '
                "15.219-8.5 20.462-5.243 5.244-12.489 8.5-20.463 8.5h-88.266v35.976h178.374c7.974 0 15.22 "
                "3.256 20.463 8.499s8.5 12.489 8.5 20.463v70.195c0 5.527-4.481 10.007-10.008 10.007-5.527 "
                "0-10.007-4.48-10.007-10.007v-70.195a8.916 8.916 0 00-2.635-6.312 8.916 8.916 0 "
                "00-6.313-2.635H266.219v79.214c0 5.527-4.48 10.007-10.007 10.007-5.527 "
                "0-10.008-4.48-10.008-10.007v-79.214H67.83a8.914 8.914 0 00-6.312 2.635l-.019-.02a8.963 8.963 "
                "0 00-2.616 6.332v70.267c0 5.527-4.481 10.007-10.008 10.007-5.527 "
                "0-10.007-4.48-10.007-10.007v-70.267c0-7.948 3.256-15.178 8.5-20.424l.02-.018-.02-.021c5.243-5.243 "
                "12.488-8.499 20.462-8.499h178.374v-35.976h-88.266c-7.974 "
                "0-15.219-3.256-20.462-8.5-5.244-5.243-8.5-12.489-8.5-20.462V28.962c0-7.974 3.256-15.219 "
                "8.5-20.463C142.719 3.256 149.964 0 157.938 0h196.547c7.974 0 15.22 3.256 20.463 8.499 5.243 "
                "5.244 8.5 12.489 8.5 20.463zM97.443 367.966v99.437c0 6.523-5.339 11.86-11.859 11.86H11.86c-6.521 "
                "0-11.86-5.34-11.86-11.86v-99.437c0-6.521 5.337-11.86 11.86-11.86h73.724c6.522 0 11.859 5.337 "
                "11.859 11.86zm207.59 0v99.437c0 6.523-5.339 11.86-11.86 11.86h-73.724c-6.52 "
                "0-11.859-5.34-11.859-11.86v-"
                "99.437c0-6.521 5.337-11.86 11.859-11.86h73.724c6.523 0 11.86 5.337 11.86 11.86zm206.967 "
                "0v99.437c0 6.523-5.339 11.86-11.86 11.86h-73.724c-6.52 0-11.859-5.34-11.859-11.86v-99.437c0-6.521 "
                "5.337-11.86 11.859-11.86h73.724c6.523 0 11.86 5.337 11.86 11.86zm-256.798-189.5a9.913 9.913 "
                "0 012.02 0h97.263a8.92 8.92 0 006.313-2.635 8.92 8.92 "
                "0 002.635-6.312V28.962c0-2.451-1.01-4.687-2.635-"
                "6.312a8.92 8.92 0 00-6.313-2.635H157.938c-2.451 0-4.687 "
                "1.01-6.312 2.635-1.625 1.625-2.635 3.861-2.635 "
                '6.312v140.557a8.92 8.92 0 002.635 6.312c1.625 1.625 3.861 2.635 6.312 2.635h97.264z" /></svg>'
            ),
            "calendar": (
                '<svg width="24" height="24" viewBox="0 0 24 24" '
                'fill="none" xmlns="http://www.w3.org/2000/svg">'
                '<rect x="3" y="4" width="18" height="16" rx="2" ry="2" '
                'stroke="currentColor" stroke-width="2" fill="none"/>'
                '<line x1="16" y1="2" x2="16" y2="6" stroke="currentColor" stroke-width="2"/>'
                '<line x1="8" y1="2" x2="8" y2="6" stroke="currentColor" stroke-width="2"/>'
                '<line x1="3" y1="10" x2="21" y2="10" stroke="currentColor" stroke-width="2"/>'
                "</svg>"
            ),
        }

        self.header_colors = {
            "blue": {
                "light": {"from": "from-sky-500", "to": "to-blue-600"},
                "dark": {"from": "dark:from-sky-600", "to": "dark:to-blue-800"},
            },
            "purple": {
                "light": {"from": "from-violet-500", "to": "to-purple-600"},
                "dark": {"from": "dark:from-violet-600", "to": "dark:to-purple-800"},
            },
            "orange": {
                "light": {"from": "from-amber-500", "to": "to-orange-600"},
                "dark": {"from": "dark:from-amber-600", "to": "dark:to-orange-800"},
            },
            "green": {
                "light": {"from": "from-green-500", "to": "to-green-600"},
                "dark": {"from": "dark:to-green-800", "to": "dark:from-green-600"},
            },
        }

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
