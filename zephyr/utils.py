from zephyr.compat import iteritems


SCHEMA = '_schema'


def is_list(value):
    """Returns True if value supports list interface; False - otherwise"""
    return isinstance(value, list)


def is_dict(value):
    """Returns True if value supports dict interface; False - otherwise"""
    return isinstance(value, dict)


def merge_errors(errors1, errors2):
    """Deeply merges two error messages. Error messages can be
    string, list of strings or dict of error messages (recursively).
    Format is the same as accepted by :exc:`ValidationError`.
    Returns new error messages.
    """
    if errors1 is None:
        return errors2
    elif errors2 is None:
        return errors1

    if isinstance(errors1, list):
        if not errors1:
            return errors2

        if isinstance(errors2, list):
            return errors1 + errors2
        elif isinstance(errors2, dict):
            return dict(
                errors2,
                **{SCHEMA: merge_errors(errors1, errors2.get(SCHEMA))}
            )
        else:
            return errors1 + [errors2]
    elif isinstance(errors1, dict):
        if isinstance(errors2, list):
            return dict(
                errors1,
                **{SCHEMA: merge_errors(errors1.get(SCHEMA), errors2)}
            )
        elif isinstance(errors2, dict):
            errors = dict(errors1)
            for k, v in iteritems(errors2):
                if k in errors:
                    errors[k] = merge_errors(errors[k], v)
                else:
                    errors[k] = v
            return errors
        else:
            return dict(
                errors1,
                **{SCHEMA: merge_errors(errors1.get(SCHEMA), errors2)}
            )
    else:
        if isinstance(errors2, list):
            return [errors1] + errors2 if errors2 else errors1
        elif isinstance(errors2, dict):
            return dict(
                errors2,
                **{SCHEMA: merge_errors(errors1, errors2.get(SCHEMA))}
            )
        else:
            return [errors1, errors2]
