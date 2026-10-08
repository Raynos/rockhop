"""Independent geometric fan measurements; these never qualify a derivative."""
import math


def dot(a, b): return sum(x*y for x, y in zip(a, b))
def sub(a, b): return [x-y for x, y in zip(a, b)]
def unit(a):
    length = math.sqrt(dot(a, a))
    return [x/length for x in a] if length else [0., 0., 0.]


def triangle(points, corner):
    a, b, c = points
    u = sub(b, a); v = sub(c, a)
    cross = [u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0]]
    x = unit(sub(points[(corner+1) % 3], points[corner]))
    y = unit(sub(points[(corner+2) % 3], points[corner]))
    return {'normal': unit(cross), 'areaM2': math.sqrt(dot(cross, cross))/2,
            'cornerAngleRadians': math.acos(max(-1., min(1., dot(x, y))))}


def fan(rows):
    return {kind: unit([sum(row['normal'][axis]*row[weight] for row in rows) for axis in range(3)])
            for kind, weight in [('angleWeighted', 'cornerAngleRadians'), ('areaWeighted', 'areaM2')]}
