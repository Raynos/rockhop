"""Bounded native-neighbor Smooth brush; no position or pose solver."""


def smooth_rows(original, adjacency, influence, factor, repeat, cutoff=.0001):
    """Keep anchors/outside exact; smooth simultaneously; then declare final FOUR.

    The native polygon-edge one-ring supplies brush neighbors. No Euclidean
    nearest points, opposite-surface transfers, bone/height classifications,
    fitted target edges, or iterative success criterion participate.
    """
    assert 0 < factor <= 1 and isinstance(repeat, int) and 0 < repeat <= 8
    current = [dict(row) for row in original]
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
    final = list(original); removed = {}
    for i in influence:
        ordered = sorted(current[i].items(), key=lambda item: (-item[1], item[0]))
        kept = [(k, v) for k, v in ordered[:4] if v > cutoff]
        total = sum(v for _, v in kept); assert total > 0
        final[i] = {k: v/total for k, v in kept}; removed[i] = 1-total
    return current, final, removed
