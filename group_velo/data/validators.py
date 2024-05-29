from django.core.exceptions import ValidationError


def length_of_five(value):
    if len(value) != 5:
        raise ValidationError("Zip code should have a length of five")


def numeric_chars(value):
    if not value.isnumeric():
        raise ValidationError(f"{value} should be numbers only")
