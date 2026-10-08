"""Small CPU-only expression algebra tests; never imports or launches Blender."""
import ast
import math
import random
import runpy
from pathlib import Path

m = runpy.run_path(str(Path(__file__).with_name('driver_math.py')))
random.seed(607)
q = lambda: m['normalized']([random.uniform(-1, 1) for _ in range(4)])
xyzw = lambda value: [value[1], value[2], value[3], value[0]]
cases = 0
allowed_functions = {'acos', 'sqrt', 'min', 'max', 'abs', 'pow'}


def check_native_subset(expression):
    # CPython eval alone accepts ** and would miss a Blender parser failure.
    for node in ast.walk(ast.parse(expression, mode='eval')):
        if isinstance(node, ast.BinOp): assert isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)), expression
        if isinstance(node, ast.Call): assert isinstance(node.func, ast.Name) and node.func.id in allowed_functions, expression


check_native_subset(m['SHAPE_EXPRESSION'])
for _ in range(50):
    rest, key = [q(), q()], [q(), q()]
    activation = {'restRelativeXYZW': list(map(xyzw, rest)), 'keyXYZW': list(map(xyzw, key)),
                  'radiusRadians': math.hypot(*(m['angle'](value, (1, 0, 0, 0)) for value in key))}
    for relative in [rest, [m['multiply'](key[i], rest[i]) for i in range(2)], [q(), q()]]:
        pelvis = q(); world = [pelvis]+[m['multiply'](pelvis, value) for value in relative]
        expected = m['expected_weight'](world, activation); properties = {}
        for name, expression, variables in m['graph'](activation, {'pelvis': 'P', 'L': 'L', 'R': 'R'}):
            check_native_subset(expression)
            inputs = {}
            for variable, spec in variables.items():
                inputs[variable] = (world[['P', 'L', 'R'].index(spec[1])]['wxyz'.index(spec[2])]
                                   if spec[0] == 'WORLD_QUATERNION' else properties[spec[1]])
            properties[name] = eval(expression, {'__builtins__': {}, 'acos': math.acos, 'sqrt': math.sqrt,
                                               'min': min, 'abs': abs}, inputs)
        actual = eval(m['SHAPE_EXPRESSION'], {'__builtins__': {}, 'max': max, 'pow': math.pow}, {'x': properties[m['PREFIX']+'x']})
        assert abs(actual-expected) < 1e-7, (actual, expected)
        cases += 1
print(f'PASS {cases} built-in driver graph / original quaternion-kernel cases, including common rotation, rest and key endpoints')
