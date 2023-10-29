import reprlib


def get_by_path(data, path, default=None):
    assert isinstance(path, list), "Path must be a list"

    rv = data
    try:
        for key in path:
            if rv is None:
                return default

            if isinstance(rv, list):
                if isinstance(key, int):
                    rv = rv[key]
                elif isinstance(key, dict):
                    matched_index = -1
                    for index, item in enumerate(rv):
                        check = True
                        for k, v in key.items():
                            # Add support for nested dicts and lists
                            if isinstance(v, list):
                                check = False if get_by_path(item.get(k, None), v) is None else True
                            elif isinstance(v, dict):
                                check = False if get_by_path(item.get(k, None), [v]) is None else True
                            elif str(item.get(k, None)) != v:
                                check = False

                            if not check:
                                break

                        if check:
                            matched_index = index
                            break
                    if matched_index == -1:
                        rv = None
                    else:
                        rv = rv[matched_index]
                else:  # pragma: no cover
                    raise TypeError(
                        "Can not lookup by {0} in list. "
                        "Possible lookups are by int or by dict.".format(
                            reprlib.repr(key)
                        )
                    )
            else:
                rv = rv[key]

        return rv
    except (IndexError, KeyError, AttributeError):
        return default


def bracket_handler(route) -> dict:
    """
    Handle the route with brackets.
    """
    temp_dict = {}
    route = route[1:-1]
    route_separate = route.split(",")
    bracket_stack = []
    real_route = []
    start, end = -1, -1

    for index, sub_route in enumerate(route_separate):
        for i in range(sub_route.count("{")):
            bracket_stack.append("{")
            if start == -1:
                start = index

        for i in range(sub_route.count("}")):
            bracket_stack.pop()

        if len(bracket_stack) == 0:
            if start != -1:
                end = index
                real_route.append(",".join(route_separate[start:end + 1]))
                start, end = -1, -1
            else:
                real_route.append(sub_route)

    for index, sub_route in enumerate(real_route):
        key = sub_route.split(":")[0].strip()
        value = ":".join(sub_route.split(":")[1:]).strip()
        if value.startswith('"'):
            value = value[1:-1]
            temp_dict[key] = value
        elif value.startswith("{"):
            temp_dict[key] = parse_route(value)[0]
        else:
            temp_dict[key] = parse_route(value)

    return temp_dict


def parse_route(route):
    """
    Parse a route string into a list of keys and/or dictionaries.
    """

    route_separate = route.split(".")
    brackets_stack = []
    start, end = -1, -1
    real_route = []

    for index, sub_route in enumerate(route_separate):
        for i in range(sub_route.count("{")):
            brackets_stack.append("{")
            if start == -1:
                start = index

        for i in range(sub_route.count("}")):
            brackets_stack.pop()

        if len(brackets_stack) == 0:
            if start != -1:
                end = index
                real_route.append(".".join(route_separate[start:end + 1]))
                start, end = -1, -1
            else:
                real_route.append(sub_route)

    for index, sub_route in enumerate(real_route):
        if sub_route.startswith("{") and sub_route.endswith("}"):
            real_route[index] = bracket_handler(sub_route)

    for index, sub_route in enumerate(real_route):
        try:
            real_route[index] = int(sub_route)
        except (ValueError, TypeError):
            pass

    return real_route
