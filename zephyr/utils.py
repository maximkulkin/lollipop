def is_list(value):
    """Returns True if value supports list interface; False - otherwise"""
    return isinstance(value, list)


def is_dict(value):
    """Returns True if value supports dict interface; False - otherwise"""
    return isinstance(value, dict)
