"""Distinct prescribed torso/sleeve offset meridians, with retained end ease.

Canonical axes and fixed apex/end correspondence choose station and angle.
Distance only solves scalar radial placement on that already chosen branch.
"""
import numpy as np


def smooth(t): return t*t*t*(10+t*(-15+6*t))


class Axis:
    """Natural C2 spline through exact canonical75 centerline landmarks."""
    def __init__(self, points):
        self.points = np.asarray(points, float)
        self.knots = np.r_[0., np.cumsum(np.linalg.norm(np.diff(self.points, axis=0), axis=1))]
        h = np.diff(self.knots); assert np.all(h > 0)
        n = len(points); matrix = np.eye(n); rhs = np.zeros_like(self.points)
        for i in range(1, n-1):
            matrix[i, i-1:i+2] = [h[i-1], 2*(h[i-1]+h[i]), h[i]]
            rhs[i] = 6*((self.points[i+1]-self.points[i])/h[i]-(self.points[i]-self.points[i-1])/h[i-1])
        self.second = np.linalg.solve(matrix, rhs)

    def at(self, station):
        k = min(len(self.points)-2, max(0, int(np.searchsorted(self.knots, station, side='right')-1)))
        h = self.knots[k+1]-self.knots[k]; b = (station-self.knots[k])/h; a = 1-b
        m0, m1 = self.second[k:k+2]; p0, p1 = self.points[k:k+2]
        p = a*p0+b*p1+((a**3-a)*m0+(b**3-b)*m1)*h*h/6
        tangent = (p1-p0)/h+((1-3*a*a)*m0+(3*b*b-1)*m1)*h/6
        return p, tangent/np.linalg.norm(tangent)

    def station(self, point):
        # Projection to a named skeletal branch establishes anatomical axial
        # correspondence. It is not a nearest-body/material reassignment.
        candidates = list(self.knots)
        ratio = (np.sqrt(5)-1)/2
        for low, high in zip(self.knots[:-1], self.knots[1:]):
            a, b = high-ratio*(high-low), low+ratio*(high-low)
            fa = np.sum((self.at(a)[0]-point)**2); fb = np.sum((self.at(b)[0]-point)**2)
            for _ in range(48):
                if fa <= fb:
                    high, b, fb = b, a, fa; a = high-ratio*(high-low); fa = np.sum((self.at(a)[0]-point)**2)
                else:
                    low, a, fa = a, b, fb; b = low+ratio*(high-low); fb = np.sum((self.at(b)[0]-point)**2)
            candidates.append((low+high)/2)
        return min(candidates, key=lambda s: np.sum((self.at(s)[0]-point)**2))


class Meridian:
    def __init__(self, axis, apex_pair, end_pair, body, nearest, minimum, precision, context):
        self.axis, self.body, self.nearest = axis, body, nearest
        self.apex_pair, self.end_pair = np.asarray(apex_pair), np.asarray(end_pair)
        self.minimum, self.precision, self.context = minimum, precision, context
        self.apex, self.end = self.apex_pair.mean(0), self.end_pair.mean(0)
        self.start, self.finish = axis.station(self.apex), axis.station(self.end)
        assert self.start != self.finish, ('Collapsed canonical branch stations', context)
        self.directions, self.radii = [], []
        for station, point in ((self.start, self.apex), (self.finish, self.end)):
            center, _ = axis.at(station); delta = point-center; radius = np.linalg.norm(delta)
            self.directions.append(delta/radius); self.radii.append(radius)
        self.eases = [float(nearest(pair)[0].min()) for pair in (self.apex_pair, self.end_pair)]
        assert min(self.eases) >= minimum, ('Fixed paired endpoint is not healthy', context, self.eases)
        self.angle = float(np.arccos(np.clip(np.dot(*self.directions), -1., 1.)))
        assert self.angle < np.pi, ('Ambiguous antipodal anatomical meridian', context)
        self.last = {}

    def frame(self, parameter):
        station = self.start+(self.finish-self.start)*parameter
        center, tangent = self.axis.at(station)
        if self.angle < np.sqrt(np.finfo(float).eps): direction = self.directions[0].copy()
        else:
            direction = (np.sin((1-parameter)*self.angle)*self.directions[0]+np.sin(parameter*self.angle)*self.directions[1])/np.sin(self.angle)
        direction -= np.dot(direction, tangent)*tangent
        length = np.linalg.norm(direction)
        assert length > 0, ('Anatomical radial frame is singular', self.context, station, center.tolist(), direction.tolist())
        direction /= length
        return station, center, direction

    def at(self, parameter, offsets):
        if parameter == 0: return self.apex_pair.copy()
        if parameter == 1: return self.end_pair.copy()
        station, center, direction = self.frame(parameter)
        desired = self.eases[0]*(1-smooth(parameter))+self.eases[1]*smooth(parameter)
        self.last = {**self.context, 'materialCurveParameter': float(parameter), 'canonicalStation': float(station),
            'center': center.tolist(), 'direction': direction.tolist(), 'desiredRetainedEaseM': desired,
            'radiusIntervalM': None}
        assert float(self.nearest(center[None])[0][0]) < 0, ('Canonical meridian axis is not inside its body branch', self.last)
        hits = self.body.ray_hits(center, direction)
        assert hits and hits[0][1] > 0, ('No outward exit on prescribed anatomical ray', self.last, hits[:4])
        lower = hits[0][0]; following = next((h for h in hits[1:] if h[1] < 0), None)
        if following is None:
            upper = float(np.max((self.body.points-center)@direction)+np.linalg.norm(offsets, axis=1).max()+desired)
            domain = 'OPEN_EXTERIOR'
        else: upper = following[0]; domain = 'INTERBODY_EXTERIOR'
        self.last.update(radiusIntervalM=[lower, upper], exteriorDomain=domain, owningBodyExitFace=hits[0][2])
        def gap(radius): return float(self.nearest(center+radius*direction+offsets)[0].min())
        # Preserve a known-radius predictor when it is feasible. A finite gap
        # can terminate at another body surface; open exterior has no such cap.
        predictor = self.radii[0]*(1-parameter)+self.radii[1]*parameter
        if lower <= predictor <= upper and gap(predictor) >= desired: feasible = predictor
        elif following is None: feasible = upper
        else: feasible = (lower+upper)/2
        assert gap(feasible) >= desired, ('Prescribed meridian has insufficient paired-wall clearance/ease', self.last, gap(feasible))
        if gap(lower) >= desired: feasible = lower
        else:
            outside = lower
            while feasible-outside > self.precision:
                value = (outside+feasible)/2
                if gap(value) >= desired: feasible = value
                else: outside = value
        destination = center+feasible*direction+offsets
        assert float(self.nearest(destination)[0].min()) >= desired
        self.last['selectedRadiusM'] = float(feasible)
        return destination

    def controls(self, rows, pairs):
        parameters = np.linspace(0, 1, 33); curve = []
        def wall(fraction):
            k = min(len(pairs)-2, int(fraction*(len(pairs)-1))); alpha = fraction*(len(pairs)-1)-k
            a, b = pairs[k][0], pairs[k+1][0]
            value = (a-a.mean(0))*(1-alpha)+(b-b.mean(0))*alpha
            return value*(1-smooth(fraction))+(self.end_pair-self.end)*smooth(fraction)
        for parameter in parameters: curve.append(self.at(float(parameter), wall(parameter)).mean(0))
        curve = np.asarray(curve); length = np.r_[0., np.cumsum(np.linalg.norm(np.diff(curve, axis=0), axis=1))]
        assert np.all(np.diff(length) > 0), ('Repeated target material station', self.context)
        length /= length[-1]; result = []
        for row, (source_pair, broad_pair, ancestry) in zip(rows[1:], pairs[1:]):
            fraction = row['fraction']; parameter = float(np.interp(fraction, length, parameters))
            offsets = (source_pair-source_pair.mean(0))*(1-smooth(parameter))+(broad_pair-broad_pair.mean(0))*smooth(parameter)
            destination = self.at(parameter, offsets)
            result.append((source_pair, destination, {'materialFraction': fraction,
                'targetCurveParameter': parameter, 'canonicalStation': self.start+(self.finish-self.start)*parameter,
                'sourcePair': source_pair.tolist(), 'targetPair': destination.tolist(), 'ancestry': ancestry,
                'actualTargetMinimumM': float(self.nearest(destination)[0].min())}))
        assert np.array_equal(result[-1][1], self.end_pair), 'Healthy50 endpoint changed'
        return result, {'canonicalStartStation': self.start, 'canonicalEndStation': self.finish,
            'apexEaseM': self.eases[0], 'healthy50EndpointEaseM': self.eases[1],
            'healthy50EndpointExact': True, 'curve': curve.tolist(), 'orderedBranch': self.context}
