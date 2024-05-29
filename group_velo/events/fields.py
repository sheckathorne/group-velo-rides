from django import forms
from django.contrib.postgres.fields import ArrayField
from django.core import exceptions
from django.db import models


class DaysOfWeek(models.IntegerChoices):
    Monday = (0, "Monday")
    Tuesday = (1, "Tuesday")
    Wednesday = (2, "Wednesday")
    Thursday = (3, "Thursday")
    Friday = (4, "Friday")
    Saturday = (5, "Saturday")
    Sunday = (6, "Sunday")


class ChoiceArrayField(ArrayField):
    def formfield(self, **kwargs):
        defaults = {
            "form_class": forms.TypedMultipleChoiceField,
            "choices": self.base_field.choices,
        }
        defaults.update(kwargs)
        return super(ArrayField, self).formfield(**defaults)

    def to_python(self, value):
        res = super().to_python(value)
        if isinstance(res, list):
            value = [self.base_field.to_python(val) for val in res]
        return value

    def validate(self, value, model_instance):
        if not self.editable:
            # Skip validation for non-editable fields.
            return

        if self.choices is not None and value not in self.empty_values:
            if set(value).issubset({option_key for option_key, _ in self.choices}):
                return
            raise exceptions.ValidationError(
                self.error_messages["invalid_choice"],
                code="invalid_choice",
                params={"value": value},
            )

        if value is None and not self.null:
            raise exceptions.ValidationError(self.error_messages["null"], code="null")

        if not self.blank and value in self.empty_values:
            raise exceptions.ValidationError(self.error_messages["blank"], code="blank")


class CharFieldAllowsMultiSelectSearch(models.CharField):
    def clean(self, value, model_instance):
        value = self.to_python(value)
        if isinstance(value, str) or value is None:
            self.validate(value, model_instance)
            self.run_validators
        elif isinstance(value, list):
            for v in value:
                self.validate(v, model_instance)
                self.run_validators(v)
        return value

    def to_python(self, value):
        if isinstance(value, str) or isinstance(value, list) or value is None:
            return value
        return str(value)
