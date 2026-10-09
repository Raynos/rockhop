"""Keep original actions intact; make complete deterministic native copies."""
import re

LIVE = 'M11_liveControls'
PATH = re.compile(r'^pose\.bones\["([^"]+)"\]\.(location|rotation_quaternion|scale)$')


def curves(action):
    assert len(action.slots) == 1
    for layer in action.layers:
        for strip in layer.strips:
            bag = strip.channelbag(action.slots[0])
            if bag:
                yield from bag.fcurves


def signature(action):
    return [{'path': curve.data_path, 'index': curve.array_index, 'extrapolation': curve.extrapolation,
             'keys': [[list(key.co), list(key.handle_left), list(key.handle_right), key.handle_left_type,
                       key.handle_right_type, key.interpolation, key.easing] for key in curve.keyframe_points]}
            for curve in curves(action)]


def eligible(action, names):
    if len(action.slots) != 1:
        return False
    found = list(curves(action))
    return bool(found) and all((match := PATH.fullmatch(curve.data_path)) and match[1] in names
        and 0 <= curve.array_index < (4 if match[2] == 'rotation_quaternion' else 3)
        and not curve.modifiers and not curve.sampled_points for curve in found)


def bag(action):
    if not action.slots:
        action.slots.new('OBJECT', 'RiderSkeleton')
    assert len(action.slots) == 1
    if not action.layers:
        return action.layers.new('Deterministic playback').strips.new(type='KEYFRAME').channelbags.new(action.slots[0])
    for layer in action.layers:
        for strip in layer.strips:
            value = strip.channelbag(action.slots[0])
            if value:
                return value
    raise AssertionError('Action has no supported channelbag')


def static_curve(channelbag, path, index, value, start, end):
    curve = channelbag.fcurves.new(path, index=index)
    curve.keyframe_points.add(2)
    curve.keyframe_points.foreach_set('co', [start, value, end, value])
    for key in curve.keyframe_points:
        key.interpolation = 'CONSTANT'
    curve.update()


def reset_tracks(action, names, start, end, mode):
    channelbag = bag(action)
    existing = {(curve.data_path, curve.array_index) for curve in curves(action)}
    added = []
    for name in names:
        for prop, values in (('location', [0, 0, 0]), ('rotation_quaternion', [1, 0, 0, 0]), ('scale', [1, 1, 1])):
            path = f'pose.bones["{name}"].{prop}'
            for index, value in enumerate(values):
                if (path, index) not in existing:
                    static_curve(channelbag, path, index, value, start, end)
                    added.append((path, index))
    mode_path = f'["{LIVE}"]'
    assert (mode_path, 0) not in existing
    static_curve(channelbag, mode_path, 0, mode, start, end)
    return added


def playback_copy(bpy, source, names):
    assert eligible(source, set(names))
    name = 'Native.'+source.name
    assert name not in bpy.data.actions
    before = signature(source)
    action = source.copy()
    action.name = name
    action.use_fake_user = True
    start, end = map(float, source.frame_range)
    assert end > start
    added = reset_tracks(action, names, start, end, 0.)
    copied = [row for row in signature(action) if (row['path'], row['index']) not in added
              and row['path'] != f'["{LIVE}"]']
    assert copied == before and signature(source) == before, 'Original native action curves changed'
    return action, {'sourceAction': source.name, 'playbackAction': name, 'frameRange': [start, end],
                    'originalCurvesExact': True, 'missingRestChannelsFilled': len(added), 'liveControls': 0.}
