from django.core.exceptions import ValidationError


class MaxRidersValidator:
    def __init__(self, registered_rider_count):
        self.registered_rider_count = registered_rider_count

    def __call__(self, value):
        if value and self.registered_rider_count and value < self.registered_rider_count:
            raise ValidationError(
                f"Cannot set max riders fewer than the number of registered riders ({self.registered_rider_count})"
            )
