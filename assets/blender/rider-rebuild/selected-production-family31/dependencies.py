"""Invert Blender's ID -> users map without following scene membership upward."""


def dependencies(user_map):
    result = {}
    for used, users in user_map.items():
        result.setdefault(used, set())
        for user in users:
            result.setdefault(user, set()).add(used)
    return result


def closure(roots, graph):
    retained = set(roots)
    pending = list(roots)
    while pending:
        for used in graph.get(pending.pop(), ()):
            if used not in retained:
                retained.add(used)
                pending.append(used)
    return retained


def removable_unused(identifier, retained, users):
    # A live reference or fake user is never forcibly cleared.
    return identifier not in retained and users == 0
