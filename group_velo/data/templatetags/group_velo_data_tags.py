from django import template
from sqids.sqids import Sqids

from config.settings.base import SQIDS_ALPHABET, SQIDS_MIN_LEN

register = template.Library()


@register.filter
def to_sqid(val):
    sqids = Sqids(alphabet=SQIDS_ALPHABET, min_length=SQIDS_MIN_LEN)
    if val:
        return sqids.encode([val])
    else:
        return None


@register.simple_tag
def split_string(str, div):
    return list(filter(None, str.split(div)))
