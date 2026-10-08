"""One shared source-volume construction; no per-vertex fitting targets."""
import json
import struct
import numpy as np


def smooth(x):
    x = np.clip(x, 0., 1.)
    return x*x*(3.-2.*x)


def apply(points, matrix):
    return np.sum(points[:, None, :]*matrix[None, :3, :3], axis=2)+matrix[:3, 3]


def rotation(a, b):
    a, b = a/np.linalg.norm(a), b/np.linalg.norm(b)
    v, c = np.cross(a, b), float(np.sum(a*b))
    assert c > -.999
    k = np.array([[0., -v[2], v[1]], [v[2], 0., -v[0]], [-v[1], v[0], 0.]])
    return np.eye(3)+k+np.sum(k[:, :, None]*k[None, :, :], axis=1)/(1.+c)


def read_hoodie(path):
    data = path.read_bytes()
    size = struct.unpack_from('<I', data, 12)[0]
    doc = json.loads(data[20:20+size])
    primitive = doc['meshes'][0]['primitives'][0]
    row = doc['accessors'][primitive['attributes']['POSITION']]
    view = doc['bufferViews'][row['bufferView']]
    points = np.ndarray((row['count'], 3), dtype='<f4', buffer=data,
        offset=28+size+view.get('byteOffset', 0)+row.get('byteOffset', 0),
        strides=(view.get('byteStride', 12), 4)).copy().astype(float)
    points = points[:, [0, 2, 1]]
    points[:, 1] *= -1
    return points


def ray_radii(origin, direction, points, faces):
    triangle = points[faces]
    e1, e2 = triangle[:, 1]-triangle[:, 0], triangle[:, 2]-triangle[:, 0]
    p = np.cross(direction, e2)
    det = np.sum(e1*p, axis=1)
    valid = np.abs(det) > 1e-15
    inv = 1./np.where(valid, det, 1.)
    s = origin-triangle[:, 0]
    u = np.sum(s*p, axis=1)*inv
    q = np.cross(s, e1)
    v = np.sum(direction*q, axis=1)*inv
    distance = np.sum(e2*q, axis=1)*inv
    return np.sort(distance[valid & (u >= 0) & (v >= 0) & (u+v <= 1)
                            & (distance > 0) & (distance < .15)])


class BodyProfile:
    """Actual wearer contours about the real native forearm centerline."""
    def __init__(self, points, faces, wrist, axis, basis_x, basis_z, settings):
        axis = np.asarray(axis, dtype=float)
        axis /= np.linalg.norm(axis)
        self.wrist, self.axis, self.x, self.z = wrist, axis, basis_x, basis_z
        self.stations = np.linspace(0., .12, settings['bodyProfileStations'])
        self.angles = np.arange(settings['bodyProfileAngles'])*2*np.pi/settings['bodyProfileAngles']
        axial = np.sum((points-wrist)*axis, axis=1)
        radial = np.linalg.norm(points-wrist-axial[:, None]*axis, axis=1)
        local = (axial >= -.015) & (axial <= .135) & (radial < .1)
        faces = faces[np.any(local[faces], axis=1)]
        self.radii = np.empty((len(self.stations), len(self.angles)))
        for i, station in enumerate(self.stations):
            for j, angle in enumerate(self.angles):
                direction = np.cos(angle)*basis_x+np.sin(angle)*basis_z
                hits = ray_radii(wrist+station*axis, direction, points, faces)
                assert len(hits), ('Anatomical centerline ray misses wearer', i, j)
                self.radii[i, j] = hits[-1]

    def at(self, axial, angle):
        angular = np.mod(angle, 2*np.pi)*len(self.angles)/(2*np.pi)
        a = np.floor(angular).astype(int) % len(self.angles)
        b, blend = (a+1) % len(self.angles), angular-np.floor(angular)
        station = np.clip(axial, self.stations[0], self.stations[-1])
        upper = np.clip(np.searchsorted(self.stations, station, side='right'), 1, len(self.stations)-1)
        lower = upper-1
        t = (station-self.stations[lower])/(self.stations[upper]-self.stations[lower])
        low = self.radii[lower, a]*(1-blend)+self.radii[lower, b]*blend
        high = self.radii[upper, a]*(1-blend)+self.radii[upper, b]*blend
        return low*(1-t)+high*t


def polygon_center(points):
    p = points[:, [0, 2]]
    cross = p[:, 0]*np.roll(p[:, 1], -1)-np.roll(p[:, 0], -1)*p[:, 1]
    assert abs(cross.sum()) > 1e-10
    return np.sum((p+np.roll(p, -1, axis=0))*cross[:, None], axis=0)/(3.*cross.sum())


def cuff_frame(guide, placement):
    linear = np.asarray(placement['initialPlacement']['linear'])
    scale = float(placement['initialPlacement']['uniformScale'])
    source_axis = -linear[:, 1]/scale
    axis = np.asarray(guide['forearmAxisWorld'], dtype=float)
    axis /= np.linalg.norm(axis)
    turn = rotation(source_axis, axis)
    basis_x = np.sum(turn*linear[:, 0][None, :], axis=1)/scale
    basis_z = np.sum(turn*linear[:, 2][None, :], axis=1)/scale
    # The recorded affine and scalar carry independent float precision. Make
    # the anatomical chart orthonormal while retaining the selected reflection.
    basis_x -= np.sum(basis_x*axis)*axis
    basis_x /= np.linalg.norm(basis_x)
    basis_z -= np.sum(basis_z*axis)*axis+np.sum(basis_z*basis_x)*basis_x
    basis_z /= np.linalg.norm(basis_z)
    return scale, basis_x, basis_z


def source_cuff(points, guide, source_wrist, scale, basis_x, basis_z):
    # Actual inner-cavity centroids, not the fitted local04/05 wall. Every
    # transverse section translates/scales as one volume, including both walls.
    ys = np.array([source_wrist[1], -.58, -.65, -.70])
    centers = np.vstack([np.asarray(source_wrist)[[0, 2]]]+[
        polygon_center(guide[f'section{i}_loop1_originalXYZ']) for i in (1, 2, 3)])
    center = np.column_stack([np.interp(-points[:, 1], -ys, centers[:, j]) for j in range(2)])
    radial_x = (points[:, 0]-center[:, 0])*scale
    radial_z = (points[:, 2]-center[:, 1])*scale
    axial = (source_wrist[1]-points[:, 1])*scale
    return axial, radial_x, radial_z


def construct_cuff(original, current, guide, source_wrist, scale, basis_x, basis_z,
                   transverse, settings):
    axial, x, z = source_cuff(original, guide, source_wrist, scale, basis_x, basis_z)
    axis = np.asarray(guide['forearmAxisWorld'], dtype=float)
    axis /= np.linalg.norm(axis)
    sx, sz = transverse['scale']
    tx, tz = transverse['translationM']
    proposed = (guide['wristWorld']+axial[:, None]*axis
                +(sx*x+tx)[:, None]*basis_x+(sz*z+tz)[:, None]*basis_z)
    alpha = smooth((settings['gloveAnatomicalJoinY']-original[:, 1])
                   /(settings['gloveAnatomicalJoinY']-settings['gloveFullSourceY']))
    result = current+alpha[:, None]*(proposed-current)
    assert np.array_equal(result[alpha == 0], current[alpha == 0])
    return result, alpha


def seat_cuff(original, source_faces, guide, source_wrist, scale, basis_x,
              basis_z, profile, cloth_reserve, settings):
    """Opposed inner-wall bearings set ONE positive transverse affine frame.

    The axial cavity floor near source Y=-.58 has a near-axial normal and is
    excluded. It is a wrist-join surface, not an 8mm cuff-radius constraint.
    Use rays through the actual open inner-cavity loops, rather than the X/Z
    coordinate of a corner vertex or an axial floor. Cardinal source bearings
    are authoring controls, not enclosure proof.
    """
    endpoint = (source_wrist[1]-settings['gloveFullSourceY'])*scale
    last_open_section = (source_wrist[1]+.70)*scale
    stations = profile.stations[(profile.stations >= endpoint)
                                & (profile.stations <= last_open_section)]
    assert len(stations) >= 2
    scales, translations, bearings = [], [], []
    for component, negative_angle, positive_angle in (
            (0, np.pi, 0.), (1, 1.5*np.pi, .5*np.pi)):
        source_radii, witnesses = [], []
        for sign in (-1, 1):
            candidates = []
            for section in (2, 3):
                polygon = guide[f'section{section}_loop1_originalXYZ']
                planar = polygon[:, [0, 2]]-polygon_center(polygon)
                edge = np.roll(planar, -1, axis=0)-planar
                direction = np.zeros(2)
                direction[component] = sign
                determinant = direction[0]*edge[:, 1]-direction[1]*edge[:, 0]
                valid = np.abs(determinant) > 1e-15
                inv = 1./np.where(valid, determinant, 1.)
                distance = (planar[:, 0]*edge[:, 1]-planar[:, 1]*edge[:, 0])*inv
                fraction = (planar[:, 0]*direction[1]-planar[:, 1]*direction[0])*inv
                hits = np.flatnonzero(valid & (distance > 0) & (fraction >= 0) & (fraction <= 1))
                assert len(hits), 'Declared open cuff section does not enclose its cavity centroid'
                hit = int(hits[np.argmin(distance[hits])])
                candidates.append((float(distance[hit]*scale), section, hit, float(fraction[hit])))
            chosen = min(candidates)
            source_radii.append(chosen[0])
            witnesses.append({'section': chosen[1], 'polygonSegment': chosen[2], 'fraction': chosen[3]})
        low, high = -source_radii[0], source_radii[1]
        reserve = cloth_reserve+settings['garmentSeparationM']
        target_low = -float(profile.at(stations, np.full(len(stations), negative_angle)).max())-reserve
        target_high = float(profile.at(stations, np.full(len(stations), positive_angle)).max())+reserve
        factor = max(1., (target_high-target_low)/(high-low))
        translation = (target_low+target_high-factor*(low+high))/2.
        scales.append(factor)
        translations.append(translation)
        bearings.append({'sourceTransverseComponent': component, 'sourceRayWitnesses': witnesses,
                         'sourceBoundsM': [low, high],
                         'targetAnatomicalBoundsM': [target_low, target_high]})
    return {'scale': scales, 'translationM': translations, 'bearings': bearings,
            'sourceFullAnnulusStartY': settings['gloveFullSourceY'],
            'limits': 'Cardinal bearing fit does not prove complete circumferential containment.'}


def construct_sleeve(original, current, source_frames, side, profile, settings, endpoint):
    # Original source-pose forearm axis; x-only cuts through the source cuff
    # obliquely and were the cause of misleading asymmetric sections.
    source = original*np.asarray(source_frames['sourceDisplayAffine']['scale'])
    source += np.asarray(source_frames['sourceDisplayAffine']['translation'])
    bone = next(b for b in source_frames['authoringBones'] if b['name'] == 'AUTHOR_Forearm.'+side)
    head, tail = np.asarray(bone['sourceHead']), np.asarray(bone['sourceTail'])
    direction = tail-head
    length = np.linalg.norm(direction)
    direction /= length
    u = np.array([0., 0., 1.])-direction[2]*direction
    u /= np.linalg.norm(u)
    v = np.cross(direction, u)
    delta = source-head
    axial = np.sum(delta*direction, axis=1)
    radial = np.linalg.norm(delta-axial[:, None]*direction, axis=1)
    own_side = source[:, 0] > 0 if side == 'L' else source[:, 0] < 0
    selected = own_side & (axial > .4*length) & (radial < .15)
    ids = np.flatnonzero(selected)
    assert len(ids) > 1000
    s = axial[ids]
    uv = np.column_stack((np.sum(delta[ids]*u, axis=1), np.sum(delta[ids]*v, axis=1)))
    knots = np.linspace(.4*length, float(s.max()), settings['sourceSleeveSections'])
    centers, inner, outer = [], [], []
    half = (knots[1]-knots[0])*.7
    for knot in knots:
        band = uv[np.abs(s-knot) <= half]
        assert len(band) >= 8, ('Insufficient original sleeve section', side, knot)
        center = (band.min(axis=0)+band.max(axis=0))/2.
        radii = np.linalg.norm(band-center, axis=1)
        centers.append(center)
        inner.append(float(radii.min()))
        outer.append(float(radii.max()))
    centers = np.asarray(centers)
    center = np.column_stack([np.interp(s, knots, centers[:, j]) for j in range(2)])
    offset = uv-center
    radius = np.linalg.norm(offset, axis=1)
    assert np.all(radius > 1e-8), 'Source sleeve chart reaches its axis; no guessed cap repair'
    lo, hi = np.interp(s, knots, inner), np.interp(s, knots, outer)
    assert np.all(hi-lo > 1e-6)
    layer = (radius-lo)/(hi-lo)
    target_axis = -profile.axis
    target_u = np.array([0., 0., 1.])-target_axis[2]*target_axis
    target_u /= np.linalg.norm(target_u)
    target_v = np.cross(target_axis, target_u)
    unit = offset[:, 0, None]/radius[:, None]*target_u+offset[:, 1, None]/radius[:, None]*target_v
    angle = np.arctan2(np.sum(unit*profile.z, axis=1), np.sum(unit*profile.x, axis=1))
    station = endpoint+(s.max()-s)/(s.max()-knots[0])*(settings['sleeveNativeTransitionM']-endpoint)
    body_radius = profile.at(station, angle)
    target_radius = body_radius+settings['clothInnerEaseM']+layer*settings['clothTerminalWallM']
    assert np.all(target_radius > 0), 'Source-layer chart is not a positive volume map'
    proposed = profile.wrist+station[:, None]*profile.axis+target_radius[:, None]*unit
    blend = smooth((settings['sleeveNativeTransitionM']-station)/(
        settings['sleeveNativeTransitionM']-settings['sleeveNativeFullConstructionM']))
    result = current.copy()
    result[ids] = current[ids]+blend[:, None]*(proposed-current[ids])
    full = blend == 1
    assert full.any()
    reserve = float(np.max(target_radius[full]-body_radius[full]))
    return result, ids[blend > 0], {
        'originalSourceChartAxis': direction.tolist(), 'sourceCenterlineKnots': knots.tolist(),
        'sourceCenterlineUV': centers.tolist(), 'sourceInnerRadius': inner, 'sourceOuterRadius': outer,
        'terminalLayerCoordinateRange': [float(layer[full].min()), float(layer[full].max())],
        'maximumActualClothReserveM': reserve, 'sleeveEndpointAxialM': float(endpoint),
        'originalSourceVerticesSelected': len(ids), 'changedVertices': int(np.sum(blend > 0)),
        'minimumFullConstructionBodyRadialClearanceM': float(np.min(target_radius[full]-body_radius[full]))}
