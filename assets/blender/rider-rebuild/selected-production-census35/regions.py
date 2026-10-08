"""Connected failed-face regions by shared edges, never merely shared points."""


def connected_regions(faces, selected):
    selected = set(map(int, selected)); by_edge = {}
    for index in sorted(selected):
        vertices = list(map(int, faces[index]))
        for a, b in zip(vertices, vertices[1:]+vertices[:1]):
            by_edge.setdefault(tuple(sorted((a, b))), []).append(index)
    adjacent = {i: set() for i in selected}
    for incident in by_edge.values():
        for index in incident: adjacent[index].update(incident)
    result = []
    while selected:
        pending = [min(selected)]; component = set()
        while pending:
            index = pending.pop()
            if index not in selected: continue
            selected.remove(index); component.add(index)
            pending.extend(adjacent[index] & selected)
        result.append(sorted(component))
    return sorted(result, key=lambda row: (-len(row), row[0]))
