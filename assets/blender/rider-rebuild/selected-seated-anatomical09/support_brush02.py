"""One named anatomical support correction, then the unchanged native brush.

No rank pruning: each selected full authored row must already fit FOUR. Root,
bilateral crotch, upper-waist spine and lower ipsilateral shin remain available.
Coalescing is valid only within the measured finite motion envelope.
"""

COALESCE = {
    'DEF-pelvis.L': 'DEF-spine', 'DEF-pelvis.R': 'DEF-spine',
    'DEF-thigh.L.001': 'DEF-thigh.L', 'DEF-thigh.R.001': 'DEF-thigh.R',
}


def coalesce(row):
    result = {}
    for name, weight in row.items():
        target = COALESCE.get(name, name)
        result[target] = result.get(target, 0.)+weight
    return result


def finish(row, cutoff):
    assert 0 < len(row) <= 4, ('Anatomical support exceeds FOUR; do not rank it', row)
    kept = {name: value for name, value in row.items() if value > cutoff}
    total = sum(kept.values()); assert total > 0
    return {name: value/total for name, value in kept.items()}, max(0., 1-total)


def smooth_rows(original, adjacency, influence, factor, repeat, cutoff=.0001):
    assert factor == .5 and repeat == 8 and cutoff == .0001
    # Map the source and its native neighbor context BEFORE the brush. Context
    # is a read-only representation; only explicit selected vertices are saved.
    current = [coalesce(row) for row in original]
    for _ in range(repeat):
        previous = current; current = list(previous)
        for i, falloff in influence.items():
            neighbors = sorted(adjacency[i]); assert neighbors and 0 < falloff <= 1
            alpha = factor*falloff; updated = {k: v*(1-alpha) for k, v in previous[i].items()}
            for j in neighbors:
                for k, v in previous[j].items():
                    updated[k] = updated.get(k, 0.)+v*alpha/len(neighbors)
            total = sum(updated.values()); assert abs(total-1) < 1e-4
            current[i] = {k: v/total for k, v in updated.items() if v > 0}
            assert len(current[i]) <= 4, ('Unexpected regional palette; stop before saving', i, current[i])
    full, final, removed = list(original), list(original), {}
    for i in influence:
        full[i] = current[i]; final[i], removed[i] = finish(current[i], cutoff)
    return full, final, removed
