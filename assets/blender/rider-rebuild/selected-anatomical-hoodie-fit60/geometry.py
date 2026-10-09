"""Small exact NumPy mesh queries for pinned section/endpoint diagnostics."""
import numpy as np


class Mesh:
    def __init__(self, points, faces):
        self.points = np.asarray(points, float); self.faces = faces
        self.triangles = self.points[faces]
        self.low, self.high = self.triangles.min(1), self.triangles.max(1)

    def nearest(self, query):
        query = np.asarray(query, float); gaps, indices = [], []
        for point in query:
            vertex_upper = np.min(np.sum((self.points-point)**2, axis=1))
            box = np.maximum(self.low-point, 0)+np.minimum(self.high-point, 0)
            ids = np.flatnonzero(np.sum(box*box, axis=1) <= vertex_upper)
            t = self.triangles[ids]; normal = np.cross(t[:, 1]-t[:, 0], t[:, 2]-t[:, 0])
            square = np.sum(normal*normal, axis=1)
            signed = np.sum((point-t[:, 0])*normal, axis=1)/np.where(square > 0, square, 1.)
            projected = point-signed[:, None]*normal
            valid = square > 0
            for a, b in ((0, 1), (1, 2), (2, 0)):
                valid &= np.sum(np.cross(t[:, b]-t[:, a], projected-t[:, a])*normal, axis=1) >= 0
            distances = np.where(valid, signed*signed*square, np.inf)
            closest = projected.copy()
            for a, b in ((0, 1), (1, 2), (2, 0)):
                edge = t[:, b]-t[:, a]; denominator = np.sum(edge*edge, axis=1)
                fraction = np.sum((point-t[:, a])*edge, axis=1)/np.where(denominator > 0, denominator, 1.)
                candidate = t[:, a]+np.clip(fraction, 0, 1)[:, None]*edge
                length = np.sum((point-candidate)**2, axis=1); better = length < distances
                distances[better] = length[better]; closest[better] = candidate[better]
            index = int(np.argmin(distances)); sign = 1 if np.dot(point-closest[index], normal[index]) >= 0 else -1
            gaps.append(sign*np.sqrt(distances[index])); indices.append(int(ids[index]))
        return np.asarray(gaps), np.asarray(indices)

    def x_hits(self, y, z, sign):
        ids = np.flatnonzero((self.low[:, 1] <= y) & (self.high[:, 1] >= y) & (self.low[:, 2] <= z) & (self.high[:, 2] >= z))
        t = self.triangles[ids]; origin = np.array([0., y, z]); direction = np.array([sign, 0., 0.])
        e1, e2 = t[:, 1]-t[:, 0], t[:, 2]-t[:, 0]; cross = np.cross(direction, e2)
        determinant = np.sum(e1*cross, axis=1); valid = abs(determinant) > np.finfo(float).eps
        inverse = 1/np.where(valid, determinant, 1.); delta = origin-t[:, 0]
        u = np.sum(delta*cross, axis=1)*inverse; q = np.cross(delta, e1)
        v = q@direction*inverse; distance = np.sum(e2*q, axis=1)*inverse
        good = np.flatnonzero(valid & (u >= 0) & (v >= 0) & (u+v <= 1) & (distance > 0))
        return sorted((float(distance[i]), float(np.cross(e1[i], e2[i])@direction), int(ids[i])) for i in good)

    def ray_hits(self, origin, direction):
        near, far = np.full(len(self.faces), -np.inf), np.full(len(self.faces), np.inf)
        valid = np.ones(len(self.faces), bool)
        for axis in range(3):
            if direction[axis] == 0:
                valid &= (self.low[:, axis] <= origin[axis]) & (self.high[:, axis] >= origin[axis])
            else:
                a = (self.low[:, axis]-origin[axis])/direction[axis]
                b = (self.high[:, axis]-origin[axis])/direction[axis]
                near = np.maximum(near, np.minimum(a, b)); far = np.minimum(far, np.maximum(a, b))
        ids = np.flatnonzero(valid & (far >= np.maximum(near, 0)))
        t = self.triangles[ids]; e1, e2 = t[:, 1]-t[:, 0], t[:, 2]-t[:, 0]
        cross = np.cross(direction, e2); determinant = np.sum(e1*cross, axis=1)
        valid = abs(determinant) > np.finfo(float).eps; inverse = 1/np.where(valid, determinant, 1.)
        delta = origin-t[:, 0]; u = np.sum(delta*cross, axis=1)*inverse
        q = np.cross(delta, e1); v = q@direction*inverse; distance = np.sum(e2*q, axis=1)*inverse
        good = np.flatnonzero(valid & (u >= 0) & (v >= 0) & (u+v <= 1) & (distance > 0))
        return sorted((float(distance[i]), float(np.cross(e1[i], e2[i])@direction), int(ids[i]),
            [float(1-u[i]-v[i]), float(u[i]), float(v[i])]) for i in good)
