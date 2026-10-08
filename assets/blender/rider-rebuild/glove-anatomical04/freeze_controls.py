"""Freeze one explicit set of mesh-edit handles from already extracted arrays.

No mesh is generated, fitted, evaluated, rendered or saved here. Cross sections
measure the actual wearer. The written coordinates are Laplacian edit handles,
not a per-vertex deformation field. Parent runs author.py once to sculpt them.
"""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
DIGITS = ('pinky', 'ring', 'middle', 'index', 'thumb')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def unit(vector):
    return vector / np.linalg.norm(vector)


def axes(forward, radial):
    y = unit(forward)
    x = unit(radial - y * np.dot(radial, y))
    return np.stack((x, y, unit(np.cross(x, y))), axis=1)


def section(points, triangles, center, frame, candidates):
    """Exact actual triangle/plane intersection; no source-target projection."""
    local = (points - center) @ frame
    polygons = local[triangles[candidates]]
    result = []
    for triangle in polygons:
        for a, b in zip(triangle, np.roll(triangle, -1, axis=0)):
            if (a[1] < 0) != (b[1] < 0):
                q = a + (b - a) * (-a[1] / (b[1] - a[1]))
                result.append(q[[0, 2]])
    assert len(result) >= 6, ('Missing actual wearer contour', center.tolist(), len(result))
    return np.asarray(result)


def ring(source, source_center, source_frame, source_width,
         target_center, target_frame, contour, padding, angles, label, uniform_scale):
    """An explicit enclosing ellipse is an editable garment cross-section.

    The selected mesh between these sparse handles retains its own sculpture.
    The cage section is a modeling measurement, never a fit/art pass.
    """
    q = (source - source_center) @ source_frame
    eligible = (abs(q[:, 1]) < .010) & (abs(q[:, 0]) < source_width)
    assert np.count_nonzero(eligible) >= 20, ('Missing selected handle section', label)
    indices = np.flatnonzero(eligible)
    xy = q[indices][:, [0, 2]]
    source_mid = (xy.min(0) + xy.max(0)) / 2
    source_radius = (xy.max(0) - xy.min(0)) / 2
    normalized = (xy - source_mid) / source_radius
    theta = np.arctan2(normalized[:, 1], normalized[:, 0])
    middle = (contour.min(0) + contour.max(0)) / 2
    radius = (contour.max(0) - contour.min(0)) / 2
    # A bounding ellipse encloses the measured contour, including asymmetric
    # thenar/palm masses. Ease is added after measuring, not used as acceptance.
    radius *= max(1., float(np.linalg.norm((contour - middle) / radius, axis=1).max()))
    radius += np.asarray(padding)
    rows = []
    for angle in angles:
        distance = abs(np.arctan2(np.sin(theta - angle), np.cos(theta - angle)))
        # Choose an actual selected surface vertex close to the explicit plane.
        score = distance + abs(q[indices, 1]) * 8
        selected = int(indices[np.argmin(score)])
        actual_angle = float(theta[np.argmin(score)])
        transverse = middle + radius * [np.cos(actual_angle), np.sin(actual_angle)]
        local_target = np.array([transverse[0], q[selected, 1] * uniform_scale, transverse[1]])
        target = target_center + target_frame @ local_target
        rows.append({'label': label + f'/angle{angle:.6f}', 'sourceVertex': selected,
                     'sourceRest': source[selected].tolist(), 'targetWorld': target.tolist(),
                     'wearerContourCount': len(contour),
                     'measuredContourBounds': [contour.min(0).tolist(), contour.max(0).tolist()],
                     'authoredCrossSectionRadius': radius.tolist(), 'easeMeters': list(padding)})
    return rows


def main():
    assert len(sys.argv) in (2, 3)
    extract_dir = Path(sys.argv[1]).resolve()
    extraction = json.loads((extract_dir / 'extract.json').read_text())
    assert extraction['operation'] == 'READ_ONLY_FITTED_MESH_EXTRACTION'
    old_inputs = json.loads((ROOT / 'assets/blender/rider-rebuild/production-gloves03/inputs.json').read_text())
    pins = {k: old_inputs[k] for k in ('nativeArrays', 'handL', 'handR', 'denseSelected',
                                      'baseColor', 'metallicRoughness', 'selectedOriginal', 'reference')}
    pins['native'] = extraction['native']
    pins['actualDigitControls'] = old_inputs['actualDigitControls']
    for key, path in {
        'originalOrbit': '.tmp/generation-comparison-2026-10-03/user-agent2/items01/gloves/orbit02/orbit.json',
        'originalOrbitRecipe': 'assets/blender/hero-remaster/generation-comparison-2026-10-03/user-agent2/items01/recipes/orbit_item.py',
        'originalDorsalView': '.tmp/generation-comparison-2026-10-03/user-agent2/items01/gloves/orbit02/frames/000.png',
        'originalPalmView': '.tmp/generation-comparison-2026-10-03/user-agent2/items01/gloves/orbit02/frames/024.png',
    }.items():
        pins[key] = {'path': path, 'sha256': sha(ROOT / path)}
    for side in ('R', 'L'):
        pins['fitted' + side] = {k: extraction['hands'][side][k] for k in ('path', 'sha256')}
    for pin in pins.values():
        assert sha(ROOT / pin['path']) == pin['sha256'], pin['path']
    source_control = json.loads((ROOT / 'assets/blender/rider-rebuild/production-gloves03/controls.json').read_text())
    source = np.load(ROOT / pins['denseSelected']['path'])['vertices'].astype(float)
    native = np.load(ROOT / pins['nativeArrays']['path'])
    names = native['jointNames'].tolist()
    lookup = {name: i for i, name in enumerate(names)}
    digit_controls = json.loads((ROOT / pins['actualDigitControls']['path']).read_text())
    angles = np.arange(8) * np.pi / 4
    result = {'acceptedArt': False, 'status': 'FROZEN_ONE_ANATOMICAL_SELECTED_SCULPT',
              'pins': pins, 'laplacianIterations': 8,
              'sourceRest': {'wrist': source_control['wrist'], 'digits': source_control['digits']},
              'method': 'One original-source uniform placement, then ordinary Laplacian mesh handles.',
              'hands': {}, 'limits': ['Explicit handles and source conservation are not wearing-fit proof.',
                                    'No bake, generic appearance shell, independent hand rig or player promotion.']}
    for side in ('R', 'L'):
        hand = np.load(ROOT / pins['hand' + side]['path'])
        fitted = np.load(ROOT / pins['fitted' + side]['path'])
        assert len(source) == len(fitted['vertices'])
        # Existing extracted selected surface has the same original index/UV
        # ancestry even though its actual shape is the rejected negative control.
        original_uv = np.load(ROOT / pins['denseSelected']['path'])['originalCornerUV'].copy()
        if side == 'L':
            original_uv = original_uv[:, ::-1]
        original_uv[:, :, 1] = 1 - original_uv[:, :, 1]
        assert np.array_equal(original_uv, fitted['blenderCornerUV'])
        head = lambda n: native['jointHeads'][lookup[n + '.' + side]]
        tail = lambda n: native['jointTails'][lookup[n + '.' + side]]
        wrist = head('DEF-hand')
        target_frame = axes(head('DEF-f_middle.01') - wrist,
                            head('DEF-f_index.01') - head('DEF-f_pinky.01'))
        curl_rows = []
        for digit in DIGITS[:-1]:
            name = f'DEF-f_{digit}.01.{side}'
            spec = digit_controls['digitFlex']['right' if side == 'R' else 'left'][name]
            world_axis = native['jointMatrices'][lookup[name]][:3, :3] @ np.asarray(spec['axisLocal'])
            curl = unit(np.cross(world_axis * spec['positiveSign'],
                                 native['jointTails'][lookup[name]] - native['jointHeads'][lookup[name]]))
            curl_rows.append((name, curl))
        # Actual selected orbit000 is source+Z and shows its knuckle pad/ribs.
        # A dorsal normal must oppose the canonical signed finger palm-curl.
        # Merely mirroring one side proves two opposite gloves, not correct
        # assignment of the selected dorsal/palm appearance on the actual hands.
        palm_curl = unit(sum(row[1] for row in curl_rows))
        if np.dot(target_frame[:, 2], palm_curl) > 0:
            target_frame[:, 2] *= -1
        def target_axes(forward):
            frame = axes(forward, target_frame[:, 0])
            if np.dot(frame[:, 2], target_frame[:, 2]) < 0:
                frame[:, 2] *= -1
            return frame
        source_wrist = np.asarray(source_control['wrist'])
        source_middle = np.asarray(source_control['digits']['middle'][0])
        source_frame = axes(source_middle - source_wrist, np.array([1., 0., 0.]))
        scale = np.linalg.norm(head('DEF-f_middle.01') - wrist) / np.linalg.norm(source_middle - source_wrist)
        linear = scale * target_frame @ source_frame.T
        initial = {'linear': linear.tolist(), 'translation': (wrist - linear @ source_wrist).tolist(),
                   'uniformScale': float(scale), 'negativeControlBounds': extraction['hands'][side]['bounds'],
                   'reflectionFromSelectedSource': bool(np.linalg.det(linear) < 0),
                   'dorsalNormal': target_frame[:, 2].tolist(),
                   'signedMCPPalmCurlChecks': [{'joint': name, 'palmCurlDirection': curl.tolist(),
                                               'selectedDorsalDotPalmCurl': float(np.dot(target_frame[:, 2], curl))}
                                              for name, curl in curl_rows]}
        assert all(row['selectedDorsalDotPalmCurl'] < -.90 for row in initial['signedMCPPalmCurlChecks'])
        handles = []
        hv, hf, hw = (hand[k] for k in ('vertices', 'faces', 'nativeCoefficients'))
        for digit in DIGITS:
            source_path = np.asarray(source_control['digits'][digit])
            stem = 'thumb' if digit == 'thumb' else 'f_' + digit
            target_path = np.asarray([head(f'DEF-{stem}.{i:02d}') for i in (1, 2, 3)]
                                     + [tail(f'DEF-{stem}.03')])
            joints = [lookup[f'DEF-{stem}.{i:02d}.{side}'] for i in (1, 2, 3)]
            mass = hw[:, joints].sum(1)
            candidates = mass[hf].mean(1) > .12
            for segment in range(3):
                for t in (0., .50):
                    # CMC is embedded in thenar, so its broad transition uses
                    # palm/web controls rather than pretending it is a tube.
                    if digit == 'thumb' and segment == 0 and t == 0:
                        continue
                    source_center = source_path[segment] * (1 - t) + source_path[segment + 1] * t
                    target_center = target_path[segment] * (1 - t) + target_path[segment + 1] * t
                    sf = axes(source_path[segment + 1] - source_path[segment], np.array([1., 0., 0.]))
                    tf = target_axes(target_path[segment + 1] - target_path[segment])
                    contour = section(hv, hf, target_center, tf, candidates)
                    handles += ring(source, source_center, sf, .125 if digit != 'thumb' else .18,
                                    target_center, tf, contour, (.0025, .003), angles,
                                    f'{digit}/segment{segment + 1}/station{t}', scale)
            # Actual selected cap and actual wearer skin endpoint are distinct
            # from the skeleton tail; this explicit cap handle covers the skin.
            sf = axes(source_path[-1] - source_path[-2], np.array([1., 0., 0.]))
            tf = target_axes(target_path[-1] - target_path[-2])
            local = (source - source_path[-1]) @ sf
            eligible = (abs(local[:, 0]) < .105) & (abs(local[:, 2]) < .2) & (local[:, 1] > -.04)
            ix = np.flatnonzero(eligible)
            tip = int(ix[np.argmax(local[ix, 1])])
            skin = (hv - target_path[-1]) @ tf
            eligible = mass > .4
            extent = float(skin[eligible, 1].max())
            target = target_path[-1] + tf[:, 1] * (extent + .003)
            handles.append({'label': digit + '/actual_skin_cap', 'sourceVertex': tip,
                            'sourceRest': source[tip].tolist(), 'targetWorld': target.tolist(),
                            'actualSkinBeyondBoneTailMeters': extent, 'easeMeters': .003})
        palm_joints = [i for i, n in enumerate(names) if n.endswith('.' + side)
                       and (n.startswith('DEF-hand') or n.startswith('DEF-palm'))]
        palm_mass = hw[:, palm_joints].sum(1)
        candidates = palm_mass[hf].mean(1) > .18
        for t in (.12, .42, .72, .96):
            sc = source_wrist * (1 - t) + source_middle * t
            tc = wrist * (1 - t) + head('DEF-f_middle.01') * t
            contour = section(hv, hf, tc, target_frame, candidates)
            handles += ring(source, sc, source_frame, .49, tc, target_frame,
                            contour, (.0035, .0045), angles, f'palm/section{t}', scale)
        # Explicit broad web/thenar controls supplement the complete sections.
        # Each target is an actual semantic web vertex, not a finger selected
        # by global nearest surface. Its source is a real selected-sculpt vertex.
        for first, second in zip(DIGITS[:-1], DIGITS[1:]):
            stems = ['thumb' if d == 'thumb' else 'f_' + d for d in (first, second)]
            masses = [hw[:, [lookup[f'DEF-{stem}.{i:02d}.{side}'] for i in (1, 2, 3)]].sum(1)
                      for stem in stems]
            a = head('DEF-' + stems[0] + '.01')
            b = head('DEF-' + stems[1] + ('.02' if second == 'thumb' else '.01'))
            center = (a + b) / 2
            candidate_ids = np.flatnonzero((masses[0] > .025) & (masses[1] > .025))
            assert len(candidate_ids) >= 8, ('Missing actual semantic web', side, first, second)
            candidate_ids = candidate_ids[np.argsort(np.linalg.norm(hv[candidate_ids] - center, axis=1))[:12]]
            a = np.asarray(source_control['digits'][first][0])
            b = np.asarray(source_control['digits'][second][1 if second == 'thumb' else 0])
            sc = (a + b) / 2
            if second != 'thumb':
                sc[1] += .08
            local = (source - sc) @ source_frame
            source_ids = np.flatnonzero((abs(local[:, 0]) < .055) & (abs(local[:, 1]) < .04))
            assert len(source_ids) > 20
            for direction in (-1., 1.):
                target_id = int(candidate_ids[np.argmax(direction * ((hv[candidate_ids] - center) @ target_frame[:, 2]))])
                source_id = int(source_ids[np.argmax(direction * local[source_ids, 2])])
                target = hv[target_id] + direction * target_frame[:, 2] * .003
                handles.append({'label': f'web/{first}_{second}/surface{direction}',
                                'sourceVertex': source_id, 'sourceRest': source[source_id].tolist(),
                                'targetWorld': target.tolist(), 'actualWearerVertex': target_id,
                                'actualMixedDigitMass': [float(m[target_id]) for m in masses],
                                'easeMeters': .003})
        thenar = head('DEF-thumb.01')
        thumb_joints = [lookup[f'DEF-thumb.{i:02d}.{side}'] for i in (1, 2, 3)]
        thumb_mass = hw[:, thumb_joints].sum(1)
        ids = np.flatnonzero((thumb_mass > .025) & (palm_mass > .1))
        ids = ids[np.argsort(np.linalg.norm(hv[ids] - thenar, axis=1))[:16]]
        assert len(ids) >= 8
        sc = np.asarray(source_control['digits']['thumb'][0])
        local = (source - sc) @ source_frame
        source_ids = np.flatnonzero((abs(local[:, 0]) < .09) & (abs(local[:, 1]) < .09))
        for direction in (-1., 1.):
            target_id = int(ids[np.argmax(direction * ((hv[ids] - thenar) @ target_frame[:, 2]))])
            source_id = int(source_ids[np.argmax(direction * local[source_ids, 2])])
            target = hv[target_id] + direction * target_frame[:, 2] * .0035
            handles.append({'label': f'thenar/CMC/surface{direction}', 'sourceVertex': source_id,
                            'sourceRest': source[source_id].tolist(), 'targetWorld': target.tolist(),
                            'actualWearerVertex': target_id, 'easeMeters': .0035})
        body_v, body_f, body_w = (native[k] for k in ('vertices', 'faces', 'nativeCoefficients'))
        forearm = [lookup['DEF-forearm.' + side], lookup['DEF-forearm.' + side + '.001']]
        mass = body_w[:, forearm + palm_joints].sum(1)
        near = np.linalg.norm(body_v - wrist, axis=1) < .13
        candidates = (mass[body_f].mean(1) > .45) & near[body_f].all(1)
        cuff_frame = target_axes(-hand['cuffProximalAxis'])
        for source_distance, target_distance in ((.13, .015), (.27, .033), (.39, .048)):
            sc = source_wrist - source_frame[:, 1] * source_distance
            tc = wrist + hand['cuffProximalAxis'] * target_distance
            contour = section(body_v, body_f, tc, cuff_frame, candidates)
            handles += ring(source, sc, source_frame, .50, tc, cuff_frame,
                            contour, (.0035, .0035), angles,
                            f'cuff/section{source_distance}', scale)
        # Unique handles have one physical destination. A ring shared with a
        # neighboring authored region uses the first explicit constraint.
        unique = {}
        for handle in handles:
            unique.setdefault(handle['sourceVertex'], handle)
        handles = list(unique.values())
        result['hands'][side] = {'initialPlacement': initial, 'handles': handles,
                                 'originalCornerUVNegativeControlParity': True,
                                 'support': 'Actual native hand/forearm triangle cross sections.'}
    path = HERE / (sys.argv[2] if len(sys.argv) == 3 else 'controls.json')
    assert path.parent == HERE and path.suffix == '.json'
    assert not path.exists(), 'Do not overwrite a frozen construction attempt'
    path.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'controls': str(path.relative_to(ROOT)), 'sha256': sha(path),
                      'handles': {s: len(result['hands'][s]['handles']) for s in ('R', 'L')}}))


if __name__ == '__main__':
    main()
