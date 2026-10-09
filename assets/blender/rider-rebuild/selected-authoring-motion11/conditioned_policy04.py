"""Pure mode policy: switch only where measured IK/FK agree at the same key."""
import math

LIMIT = .0001


def conditioned_modes(ik_error, fk_error, difference, limit=LIMIT):
    assert len(ik_error) == len(fk_error) == len(difference) and ik_error
    assert all(math.isfinite(value) and value >= 0 for rows in (ik_error, fk_error, difference) for value in rows)
    assert all(value < limit for value in fk_error), 'FK source replay itself fails; conditioning cannot excuse it'
    modes = [1]*len(ik_error)
    intervals = []
    index = 0
    while index < len(ik_error):
        if ik_error[index] < limit:
            index += 1
            continue
        first = index
        while index+1 < len(ik_error) and ik_error[index+1] >= limit:
            index += 1
        last = index
        enter = max(0, first-1)
        while enter > 0 and difference[enter] >= limit:
            enter -= 1
        leave = last+1
        while leave < len(ik_error) and difference[leave] >= limit:
            leave += 1
        for frame in range(enter, leave):
            modes[frame] = 0
        intervals.append({'firstFailingFrame': first+1, 'lastFailingFrame': last+1,
                          'fkFirstFrame': enter+1, 'ikReturnFrame': leave+1 if leave < len(modes) else None})
        index += 1
    switches = [i for i in range(1, len(modes)) if modes[i] != modes[i-1]]
    assert all(difference[i] < limit for i in switches)
    assert all(mode == 0 or ik_error[i] < limit for i, mode in enumerate(modes))
    return {'modes': modes, 'intervals': intervals, 'switchFrames': [i+1 for i in switches],
            'maximumSwitchBranchDifferenceM': max((difference[i] for i in switches), default=0.)}
