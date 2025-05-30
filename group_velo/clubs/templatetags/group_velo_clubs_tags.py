from django import template
from django.template.defaultfilters import stringfilter

from group_velo.data.choices import RequestStatus

register = template.Library()


# @register.simple_tag
# def club_border_style(loop_count, club_count):
#     border_class = ""

#     if loop_count == 1:
#         border_class += " rounded-t-xl"

#     return border_class


@register.simple_tag
def say_deactivate(tab_type, active):
    return tab_type == active or active


@register.simple_tag
def contains_pending_requests(items):
    for item in items:
        if item.status == RequestStatus.Pending:
            return True
    return False


def ride_count_of(user, ride_count):
    user_ride_count = 0
    ride_count_qs = ride_count.filter(user=user).values_list("ride_count", flat=True)
    if ride_count_qs.exists():
        user_ride_count = ride_count_qs.first()
    return user_ride_count


@register.simple_tag
def rank_ride_count(ride_count, user):
    user_ride_count = ride_count_of(user, ride_count)
    if user_ride_count > 0:
        rank = str(ride_count.filter(ride_count__gt=user_ride_count).count() + 1)
    else:
        rank = "N/A"
    return {"rank": rank, "ride_count": user_ride_count}


@register.filter
@stringfilter
def abbreviate(value):
    abbreviation = ""
    lengths = []
    words = value.upper().split()
    words_to_use = []

    if len(words) == 1:
        return words[0][0:5].upper()

    if len(words) > 5:
        for word in words:
            lengths.append(len(word))

        lengths.sort(reverse=True)
        length = lengths[4]

        for word in words:
            if len(word) >= length:
                words_to_use.append(word)
    else:
        words_to_use = words

    for word in words_to_use:
        abbreviation += word[0]

    return abbreviation
