from group_velo.events.models import EmailType, EventOccurence


def post_event_occurence_save(sender, instance, created, **kwargs):
    if not created:
        # If the ride size increased, promote waitlist riders
        instance.promote_from_waitlist_to_ride()

        # Notify the riders of any changes to the ride
        instance.notify_member_list(
            instance.modified_by,
            EmailType.MODIFY,
            custom_message=generate_email_message(instance),
            original_ride_date=instance.previous_ride_date,
        )


def remember_data(sender, instance, **kwargs):
    try:
        old_instance = EventOccurence.objects.get(id=instance.id)
    except EventOccurence.DoesNotExist:  # to handle initial object creation
        return None

    instance.previous_ride_date = old_instance.ride_date
    instance.previous_ride_time = old_instance.ride_time
    instance.previous_lower_pace_range = old_instance.lower_pace_range
    instance.previous_upper_pace_range = old_instance.upper_pace_range
    instance.previous_group_classification = old_instance.group_classification


def generate_email_message(instance):
    fields = track_fields()
    changes = []
    change_count = 0

    for field in fields:
        if getattr(instance, field["previous_name"]) != getattr(instance, field["name"]):
            change_count += 1
            field_description = field["description"].capitalize()
            original_value = getattr(instance, field["previous_name"])
            new_value = getattr(instance, field["name"])
            changes.append(f"{field_description} changed from {original_value} to {new_value}")

    if change_count == 0:
        return
    elif change_count >= 1:
        custom_message = f"The following details of {instance.occurence_name} originally scheduled for "
        f"{instance.previous_ride_date} have changed: <ul>"
        for change in changes:
            custom_message = custom_message + f"<li><i class='fa-solid fa-caret-right mr-2'></i>{change}</li>"
        custom_message = custom_message + "</ul>"
        return custom_message


def track_fields():
    return [
        {
            "name": "ride_date",
            "previous_name": "previous_ride_date",
            "description": "ride date",
            "comparison": {
                "type": "date",
                "greater": "is later",
                "less": "is earlier",
            },
            "formatter": "date",
        },
        {
            "name": "ride_time",
            "previous_name": "previous_ride_time",
            "description": "ride time",
            "comparison": {
                "type": "time",
                "greater": "is later",
                "less": "is earlier",
            },
            "formatter": "time",
        },
        {
            "name": "lower_pace_range",
            "previous_name": "previous_lower_pace_range",
            "description": "lower pace range",
            "comparison": {
                "type": "integer",
                "greater": "increased",
                "less": "decreased",
            },
            "formatter": None,
        },
        {
            "name": "upper_pace_range",
            "previous_name": "previous_upper_pace_range",
            "description": "upper pace range",
            "comparison": {
                "type": "integer",
                "greater": "increased",
                "less": "decreased",
            },
            "formatter": None,
        },
        {
            "name": "group_classification",
            "previous_name": "previous_group_classification",
            "description": "ride classification",
            "comparison": {
                "type": "ride_classification",
                "greater": "increased",
                "less": "decreased",
            },
            "formatter": None,
        },
    ]
