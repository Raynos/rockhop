"""Condition actual radial queries before the BVH's float32 conversion.

The public hit_radius(tree, world_origin, direction) signature is unchanged.
Trees contain the same retained triangles, translated by the actual wrist.
A BVH miss receives a finite float64 triangle query, never a fabricated radius.
"""
import json

import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

receipts = []


class WristLocalTree:
    def __init__(self, points, faces, wrist, axis, label):
        self.wrist = np.asarray(wrist, dtype=float).copy()
        self.axis = np.asarray(axis, dtype=float).copy()
        self.axis /= np.linalg.norm(self.axis)
        self.points = np.asarray(points, dtype=float)-self.wrist
        self.faces = np.asarray(faces, dtype=int).copy()
        self.bvh = BVHTree.FromPolygons([Vector(p) for p in self.points],
                                       self.faces.tolist(), all_triangles=True)
        axial = np.sum(self.points*self.axis, axis=1)
        bounds = axial[self.faces]
        self.lower, self.upper = bounds.min(axis=1), bounds.max(axis=1)
        self.edges = np.linspace(float(self.lower.min()), float(self.upper.max()), 129)
        assert self.edges[-1] > self.edges[0]
        # Inclusive overlapping bins only accelerate exact triangle tests.
        # A finite segment can touch more than one bin; no triangle is relabeled.
        self.bins = [np.flatnonzero((self.lower <= high) & (self.upper >= low))
                     for low, high in zip(self.edges[:-1], self.edges[1:])]
        self.receipt = {
            'label': label, 'wristWorld': self.wrist.tolist(),
            'actualTriangleCount': len(self.faces), 'distanceLimitM': .3,
            'queries': 0, 'conditionedBVHHits': 0, 'finiteTriangleFallbacks': 0,
            'finiteTriangleFallbackHits': 0, 'finiteTriangleMisses': 0,
            'firstFallbacks': [],
            'limits': 'Wrist-relative float32 BVH; actual float64 triangles on a miss. Finite sampled bearings do not replace actual geometry or moving-art checks.',
        }
        receipts.append(self.receipt)

    def finite_triangle_hit(self, origin, direction, distance):
        """Nearest actual triangle on the bounded ray; no barycentric slack."""
        start = float(origin@self.axis)
        end = start+distance*float(direction@self.axis)
        # Broadphase expansion alone accounts for dot-product rounding. This
        # does not alter the final ray/triangle test or any construction bound.
        low, high = min(start, end)-1e-12, max(start, end)+1e-12
        if high < self.edges[0] or low > self.edges[-1]:
            return None, None, None, None
        first = max(0, int(np.searchsorted(self.edges, low, side='left'))-1)
        last = min(len(self.bins)-1, int(np.searchsorted(self.edges, high, side='right'))-1)
        selected = self.bins[first] if first == last else np.unique(np.concatenate(self.bins[first:last+1]))
        if not len(selected):
            return None, None, None, None
        triangle = self.points[self.faces[selected]]
        e1, e2 = triangle[:, 1]-triangle[:, 0], triangle[:, 2]-triangle[:, 0]
        p = np.cross(direction, e2)
        determinant = np.sum(e1*p, axis=1)
        nonparallel = determinant != 0
        inverse = 1/np.where(nonparallel, determinant, 1)
        s = origin-triangle[:, 0]
        u = np.sum(s*p, axis=1)*inverse
        q = np.cross(s, e1)
        v = np.sum(direction*q, axis=1)*inverse
        along = np.sum(e2*q, axis=1)*inverse
        valid = nonparallel & (u >= 0) & (v >= 0) & (u+v <= 1)
        valid &= (along > 0) & (along <= distance)
        found = np.flatnonzero(valid)
        if not len(found):
            return None, None, None, None
        chosen = int(found[np.argmin(along[found])])
        radius = float(along[chosen])
        normal = np.cross(e1[chosen], e2[chosen])
        normal /= np.linalg.norm(normal)
        return origin+radius*direction, normal, int(selected[chosen]), radius

    def ray_cast(self, world_origin, direction, distance=.3):
        # Do this subtraction BEFORE constructing any mathutils.Vector.
        origin = np.asarray(world_origin, dtype=float)-self.wrist
        direction = np.asarray(direction, dtype=float)
        length = float(np.linalg.norm(direction))
        assert np.isfinite(length) and abs(length-1) < 1e-6
        direction = direction/length
        assert distance == .3, 'The original finite ray limit is fixed'
        self.receipt['queries'] += 1
        hit = self.bvh.ray_cast(Vector(origin), Vector(direction), distance)
        if hit[0] is not None:
            self.receipt['conditionedBVHHits'] += 1
        else:
            self.receipt['finiteTriangleFallbacks'] += 1
            hit = self.finite_triangle_hit(origin, direction, distance)
            key = 'finiteTriangleFallbackHits' if hit[0] is not None else 'finiteTriangleMisses'
            self.receipt[key] += 1
            if len(self.receipt['firstFallbacks']) < 8:
                witness = {'worldOrigin': np.asarray(world_origin).tolist(),
                           'direction': direction.tolist(), 'triangleId': hit[2],
                           'distanceM': hit[3]}
                self.receipt['firstFallbacks'].append(witness)
                print('FINITE_RAY_FALLBACK '+json.dumps({'label': self.receipt['label'], **witness}), flush=True)
        if hit[0] is None:
            return None, None, None, None
        # Match the BVH public tuple contract: position in the caller's world,
        # unchanged direction/normal frame, triangle index, Euclidean distance.
        world_hit = np.asarray(hit[0], dtype=float)+self.wrist
        return Vector(world_hit), Vector(hit[1]), int(hit[2]), float(hit[3])


def tree(points, faces, wrist, axis, label):
    return WristLocalTree(points, faces, wrist, axis, label)


def hit_radius(bvh, origin, direction):
    assert isinstance(bvh, WristLocalTree), 'All contact trees must share the conditioned query'
    hit = bvh.ray_cast(origin, direction, .3)
    return None if hit[0] is None else float(hit[3])
