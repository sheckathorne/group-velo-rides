import urllib.parse

from django import template

from group_velo.data.choices import SurfaceType

register = template.Library()


@register.simple_tag
def add_params_dict_to_string(params, new_param_name, new_param_value):
    params = {k: v for k, v in params.items()}
    params[new_param_name] = new_param_value
    return urllib.parse.urlencode(params)


@register.simple_tag
def params_dict_to_string(param_name, param_val, params):
    new_params = dict(params.copy())
    for name in param_name:
        if name == "group_classification":
            for k, v in new_params.items():
                if k in param_name:
                    if param_val in v:
                        v.remove(param_val)
        else:
            new_params.pop(name)

    return urllib.parse.urlencode(new_params, doseq=True)


@register.simple_tag
def saved_filter_model_to_dict(saved_filter):
    result = {}
    for k, v in saved_filter.filter_dict.items():
        if k == "club":
            v = saved_filter.filter_dict["club_name"]
            for c in v:
                if k in result.keys():
                    result[k] = f"{result[k]} / {c}"
                else:
                    result[k] = c
        elif k == "group_classification":
            for gc in v:
                if k in result.keys():
                    result[k] = f"{result[k]} / {gc}"
                else:
                    result[k] = gc
        elif k == "surface_type":
            for st in v:
                result[k] = SurfaceType(st).label
        elif k == "drop_designation":
            for dd in v:
                result[k] = "Yes" if dd == "1" else "No"
        else:
            for d in v:
                if k in result.keys():
                    result[k] = f"{result[k]} / {d}"
                else:
                    result[k] = d

    return result


@register.simple_tag
def saved_filter_dict_to_query_params(filter_dict):
    new_filter_dict = filter_dict.copy()
    if "club_name" in new_filter_dict.keys():
        new_filter_dict.pop("club_name")
    return urllib.parse.urlencode(new_filter_dict, doseq=True)


@register.simple_tag
def parse_message_tags(tags=[]):
    default_tags = ["debug", "info", "success", "warning", "error"]
    tags_list = tags.split(" ")
    tags_dict = {}
    for tag in tags_list:
        if tag not in default_tags and "-" in tag:
            parsed_tag = tag.split("-")
            tags_dict[parsed_tag[0]] = parsed_tag[1]

    return tags_dict
