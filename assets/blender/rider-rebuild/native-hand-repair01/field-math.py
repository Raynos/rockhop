"""Source-ID-local native field blending and deterministic four-slot reduction."""
import numpy as np


def normalized(row):
    total = sum(weight for _, weight in row)
    assert total > 1e-12 and all(np.isfinite(w) and w > 0 for _, w in row)
    assert len({name for name, _ in row}) == len(row)
    return {name: weight / total for name, weight in row}


def blend_fields(old_full, old_four, new_full, alpha, names, helpers):
    """Preserve zero-alpha row objects verbatim; normalize only modified rows."""
    assert len(old_full) == len(old_four) == len(new_full) == len(alpha)
    full, four, loss = [], [], []
    names = set(names)
    for vertex, amount in enumerate(alpha):
        assert 0 <= amount <= 1
        if amount == 0:
            full.append(old_full[vertex]); four.append(old_four[vertex]); loss.append(0.)
            continue
        old, new = normalized(old_full[vertex]), normalized(new_full[vertex])
        assert set(old) | set(new) <= names - set(helpers)
        row = sorted([[name, (1-amount)*old.get(name, 0.) + amount*new.get(name, 0.)]
                      for name in set(old) | set(new)], key=lambda r: (-r[1], r[0]))
        row = [r for r in row if r[1] > 0]
        retained = sum(weight for _, weight in row[:4])
        assert retained > 0
        full.append(row)
        four.append([[name, weight/retained] for name, weight in row[:4]])
        loss.append(sum(weight for _, weight in row[4:]))
    return full, four, np.array(loss)


def proper_frame(head, tail, palm_normal):
    y = np.asarray(tail) - head; y /= np.linalg.norm(y)
    z = np.asarray(palm_normal) - y * np.dot(palm_normal, y)
    z /= np.linalg.norm(z)
    x = np.cross(y, z)
    frame = np.column_stack((x, y, z))
    assert np.max(abs(frame.T @ frame - np.eye(3))) < 1e-12
    assert abs(np.linalg.det(frame) - 1) < 1e-12
    return frame


def flex_axis(head, tail, palm_normal, frame):
    direction = np.asarray(tail) - head; direction /= np.linalg.norm(direction)
    world = np.cross(direction, palm_normal); world /= np.linalg.norm(world)
    # Positive right-handed rotation moves the distal axis toward measured palm.
    assert np.dot(np.cross(world, direction), palm_normal) > 0
    return frame.T @ world
