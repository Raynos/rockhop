"""Built-in Blender driver expressions for corrective06; no bpy/namespace code.

Quaternion inputs are WXYZ. JSON is XYZW. No bike/camera/surface inputs.
The distance identity is angle(relative*inverse(rest), key) ==
angle(relative, key*rest), so the graph needs only relative quaternion dots.
"""
import math


def normalized(q):
    assert len(q) == 4 and all(math.isfinite(x) for x in q)
    length = math.sqrt(sum(x*x for x in q)); assert length > 1e-12
    return tuple(x/length for x in q)


def wxyz(q):
    return normalized((q[3], q[0], q[1], q[2]))


def multiply(a, b):
    w, x, y, z = a; v, i, j, k = b
    return (w*v-x*i-y*j-z*k, w*i+x*v+y*k-z*j,
            w*j-x*k+y*v+z*i, w*k+x*j-y*i+z*v)


def inverse(a):
    w, x, y, z = normalized(a); return (w, -x, -y, -z)


def angle(a, b):
    a, b = normalized(a), normalized(b)
    return 2*math.acos(min(1., abs(sum(x*y for x, y in zip(a, b)))))


def expected_weight(world, activation):
    pelvis, left, right = map(normalized, world)
    distances = []
    for i, thigh in enumerate((left, right)):
        relative = multiply(inverse(pelvis), thigh)
        flex = multiply(relative, inverse(wxyz(activation['restRelativeXYZW'][i])))
        distances.append(angle(flex, wxyz(activation['keyXYZW'][i])))
    x = math.hypot(*distances)/activation['radiusRadians']
    return max(0., 1-x)**4*(4*x+1)


PREFIX = 'ssc06_'
COMPONENTS = {
    'w': 'pw*tw+px*tx+py*ty+pz*tz',
    'x': 'pw*tx-px*tw-py*tz+pz*ty',
    'y': 'pw*ty+px*tz-py*tw-pz*tx',
    'z': 'pw*tz-px*ty+py*tx-pz*tw',
}


def graph(activation, roles):
    """Ordered DAG specs: quaternion components, hip distances, bilateral x."""
    radius = activation['radiusRadians']; assert math.isfinite(radius) and radius > 0
    rows = []
    for index, side in enumerate(('L', 'R')):
        transform_variables = {prefix+axis: ('WORLD_QUATERNION', bone, axis)
            for prefix, bone in [('p', roles['pelvis']), ('t', roles[side])]
            for axis in 'wxyz'}
        for axis, expression in COMPONENTS.items():
            rows.append((PREFIX+side+axis, expression, transform_variables))
        target = normalized(multiply(wxyz(activation['keyXYZW'][index]), wxyz(activation['restRelativeXYZW'][index])))
        dot = '+'.join(f'q{axis}*({value:.17g})' for axis, value in zip('wxyz', target))
        rows.append((PREFIX+side+'distance', f'2*acos(min(1,abs({dot})))',
                     {'q'+axis: ('PROPERTY', PREFIX+side+axis) for axis in 'wxyz'}))
    rows.append((PREFIX+'x', f'sqrt(dl*dl+dr*dr)/({radius:.17g})',
                 {'dl': ('PROPERTY', PREFIX+'Ldistance'), 'dr': ('PROPERTY', PREFIX+'Rdistance')}))
    assert all(len(expression) < 256 for _, expression, _ in rows)
    return rows


SHAPE_EXPRESSION = 'max(0,1-x)**4*(4*x+1)'
