from django import template
from django.urls import reverse
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def event_join_status(user, event_occurence):
    return {
        "can_register_to_ride": event_occurence.can_be_joined_by(user),
        "ride_is_full": event_occurence.ride_is_full(),
    }


@register.simple_tag
def registration_urls():
    return {
        "registered": reverse("events:my_rides"),
        "waitlisted": reverse("events:my_waitlist"),
    }


@register.simple_tag
def can_register_to_ride(user, event_occurence):
    return event_occurence.can_be_joined_by(user)


@register.simple_tag
def float_division_percentage(numerator, denominator):
    return (int(numerator) / int(denominator)) * 100


@register.simple_tag
def strava_or_rwgps_in(url):
    good_urls = ["strava.com", "ridewithgps.com"]
    for good_url in good_urls:
        if good_url in url:
            return True
    return False


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


def parse_external(url):
    url_path = url[url.find(".com") + 5 :]
    slash = url_path.find("/")
    return url_path[0 : slash - 1], url_path[slash + 1 :]


@register.simple_tag
def embedded_map_from(url, height=350):
    if "ridewithgps.com" in url:
        embed_type, embed_id = parse_external(url)
        embedded_map = (
            f"<iframe "
            f'src="https://ridewithgps.com/embeds?type={embed_type}&id={embed_id}" '
            f'class="w-full max-w-full h-[{height}px] border-none" scrolling="no">'
            f"</iframe>"
        )
    elif "strava.com" in url:
        embed_type, embed_id = parse_external(url)
        if embed_type == "activitie":
            embed_type = "activity"

        embedded_map = (
            f"<div "
            f'class="strava-embed-placeholder" '
            f'data-embed-type="{embed_type}" '
            f'data-embed-id="{embed_id}">'
            f'</div><script src="https://strava-embeds.com/embed.js"></script>'
        )
    else:
        embedded_map = ""

    return mark_safe(embedded_map)


@register.filter
def multiply(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return ""


@register.filter
def initials(value):
    if not value:
        return ""
    words = value.split()
    return "".join(word[0] for word in words if word)


@register.filter
def integer_to_hour_text(val):
    if not val:
        return "12 AM"

    if val == 0:
        return "12 AM"
    elif val > 0 and val < 12:
        return f"{val} AM"
    elif val == 12:
        return "12 PM"
    else:
        return f"{val - 12} PM"


@register.filter
def temperature_text_color(temp):
    default = "text-gray-900 dark:text-gray-300"
    if not temp:
        return default

    temp = int(temp)

    ranges = [
        (None, 30, "text-violet-700"),
        (30, 35, "text-indigo-600"),
        (35, 40, "text-blue-600"),
        (40, 45, "text-cyan-500"),
        (45, 50, "text-teal-500"),
        (50, 55, "text-emerald-500"),
        (55, 60, "text-green-500"),
        (60, 65, "text-lime-500"),
        (65, 70, "text-yellow-400"),
        (70, 75, "text-amber-500"),
        (75, 80, "text-orange-500"),
        (80, 85, "text-red-500"),
        (85, 90, "text-rose-600"),
        (90, 95, "text-red-800"),
        (95, 100, "text-rose-900"),
        (100, None, "text-red-950"),
    ]

    for low, high, color in ranges:
        if (low is None or temp >= low) and (high is None or temp < high):
            return color

    return default
