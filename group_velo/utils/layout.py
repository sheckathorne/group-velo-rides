from crispy_forms.layout import Field
from crispy_forms.utils import TEMPLATE_PACK


class IconPrefixedField(Field):
    def __init__(self, *args, icon_path="", **kwargs):
        self.icon_path = icon_path
        super().__init__(*args, **kwargs)

    def render(self, form, context, template_pack=TEMPLATE_PACK, extra_context=None, **kwargs):
        if extra_context is None:
            extra_context = {}
        if self.wrapper_class:
            extra_context["wrapper_class"] = self.wrapper_class
        if self.icon_path:
            context["icon_path"] = self.icon_path

        template = self.template

        return self.get_rendered_fields(
            form,
            context,
            template_pack,
            template=template,
            attrs=self.attrs,
            extra_context=extra_context,
            **kwargs,
        )
