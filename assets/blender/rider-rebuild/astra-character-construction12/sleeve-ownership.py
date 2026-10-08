"""Original sleeve wall ownership between TWO measured annulus cuts.

This is exact source face adjacency in the clipped band, not radial wall labels.
The helper is reusable by the native constructor. No selected source is edited.
"""
import hashlib
import json
import runpy
import sys
from collections import defaultdict, deque
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pin(row):
    p = ROOT/row['path']
    assert sha(p) == row['sha256'], row['path']
    return p


def clipped_topology(xyz, faces, weld, scalar, ids, lower, upper):
    """Exact inherited edge identities for a two-plane-clipped face complex."""
    edge_rows = defaultdict(list); vertices = set(); polygon_count = 0
    welded_scalar = np.empty(int(weld.max())+1); welded_scalar[weld] = scalar
    empty = []
    for face_id in ids:
        face = faces[face_id]
        polygon = [(xyz[v], np.eye(3)[i], ('v', int(weld[v]))) for i, v in enumerate(face)]
        for plane, station, sign in ((0, lower, 1), (1, upper, -1)):
            result = []
            for a, b in zip(polygon, polygon[1:]+polygon[:1]):
                da = sign*(float(np.sum(a[1]*scalar[face]))-station)
                db = sign*(float(np.sum(b[1]*scalar[face]))-station)
                if da >= 0:
                    result.append(a)
                if da*db < 0:
                    t = da/(da-db); bary = a[1]+t*(b[1]-a[1])
                    parents = [int(weld[face[j]]) for j in np.flatnonzero(bary != 0)]
                    assert len(parents) == 2, ('Parallel cuts must intersect inherited source edges', int(face_id), bary.tolist())
                    key = ('cut', plane, *sorted(parents))
                    result.append((a[0]+t*(b[0]-a[0]), bary, key))
            polygon = result
        unique = []
        for point in polygon:
            if not unique or unique[-1][2] != point[2]:
                unique.append(point)
        if len(unique) > 1 and unique[0][2] == unique[-1][2]:
            unique.pop()
        if len(unique) < 3:
            empty.append(int(face_id)); continue
        area = sum(np.linalg.norm(np.cross(unique[i][0]-unique[0][0], unique[i+1][0]-unique[0][0]))/2 for i in range(1, len(unique)-1))
        assert area > 0, ('Zero clipped area', int(face_id))
        polygon_count += 1
        for a, b in zip(unique, unique[1:]+unique[:1]):
            va, vb = a[2], b[2]; vertices.update((va, vb))
            key = tuple(sorted((va, vb)))
            edge_rows[key].append((int(face_id), 1 if va == key[0] else -1))
    assert not empty, ('Eligible face lacks positive clipped area', empty[:12])
    nonmanifold = [rows for rows in edge_rows.values() if len(rows) > 2]
    orientation = [rows for rows in edge_rows.values() if len(rows) == 2 and rows[0][1] == rows[1][1]]
    graph = defaultdict(list)
    for (a, b), rows in edge_rows.items():
        if len(rows) == 1:
            graph[a].append(b); graph[b].append(a)
    bad = [str(v) for v, neighbors in graph.items() if len(neighbors) != 2]
    unseen = set(graph); loops = 0; loop_planes = []
    while unseen:
        first = next(iter(unseen)); seen = {first}; queue = deque([first]); unseen.remove(first)
        while queue:
            for other in graph[queue.popleft()]:
                if other in unseen:
                    unseen.remove(other); seen.add(other); queue.append(other)
        loops += 1
        planes = {v[1] for v in seen if v[0] == 'cut'}
        for v in seen:
            if v[0] == 'v':
                planes.update(i for i, station in enumerate((lower, upper)) if welded_scalar[v[1]] == station)
        loop_planes.append(sorted(planes))
    return {'vertices': len(vertices), 'edges': len(edge_rows), 'polygons': polygon_count,
            'eulerCharacteristic': len(vertices)-len(edge_rows)+polygon_count,
            'boundaryLoops': loops, 'boundaryLoopCutPlanes': loop_planes,
            'nonmanifoldEdges': len(nonmanifold), 'inconsistentOrientedEdges': len(orientation),
            'badBoundaryVertexDegrees': bad[:12], 'allClippedFacesPositiveArea': True}


def band_ownership(source, faces, controls, topology, section_arrays, side):
    xyz = source*np.asarray(controls['sourceDisplayAffine']['scale'])+np.asarray(controls['sourceDisplayAffine']['translation'])
    bone = next(b for b in controls['authoringBones'] if b['name'] == 'AUTHOR_Forearm.'+side)
    head = np.asarray(bone['sourceHead']); axis = np.asarray(bone['sourceTail'])-head; axis /= np.linalg.norm(axis)
    scalar = np.sum((xyz-head)*axis, axis=1)
    sections = topology['sides'][side]['sections']
    lower, upper = [float(sections[i]['stationM']) for i in (0, 7)]
    assert lower < upper and all(sections[i]['closed'] and sections[i]['loopCount'] == 2 for i in (0, 7))
    _, weld = np.unique(source, axis=0, return_inverse=True)
    folded = np.sort(weld[faces], axis=1)
    distinct = np.all(np.diff(folded, axis=1) != 0, axis=1)
    distances = scalar[faces]
    own = xyz[:, 0] > 0 if side == 'L' else xyz[:, 0] < 0
    in_band = np.all(own[faces], axis=1) & (distances.max(axis=1) > lower) & (distances.min(axis=1) < upper)
    eligible = np.flatnonzero(in_band & distinct)
    excluded = np.flatnonzero(in_band & ~distinct)
    edge_faces = defaultdict(list)
    for i in eligible:
        face = faces[i]
        for a, b in zip(face, np.roll(face, -1)):
            # Two source faces remain adjacent only if their actual common
            # edge has positive length in the OPEN axial band after both cuts.
            if min(scalar[a], scalar[b]) < upper and max(scalar[a], scalar[b]) > lower and weld[a] != weld[b]:
                key = tuple(sorted((int(weld[a]), int(weld[b]))))
                edge_faces[key].append(int(i))
    nonmanifold = [rows for rows in edge_faces.values() if len(rows) > 2]
    assert not nonmanifold, ('Nonmanifold source band', side, nonmanifold[:4])
    graph = defaultdict(list)
    for rows in edge_faces.values():
        if len(rows) == 2:
            a, b = rows; graph[a].append(b); graph[b].append(a)
    seeds = {}
    for section in (0, 7):
        signs = [loop['signedAreaM2FromSourceWinding'] for loop in sections[section]['loops']]
        loops = sections[section]['loops']
        outer_index = max(range(2), key=lambda i: loops[i]['unsignedAreaM2'])
        inner_index = 1-outer_index
        assert outer_index in loops[inner_index]['allVerticesInsideLoops'] and signs[outer_index]*signs[inner_index] < 0
        for kind, index in (('outer', outer_index), ('inner', inner_index)):
            seeds[f'{kind}{section}'] = set(section_arrays[f'section{section}_loop{index}_sourceFaces'].tolist())
    unseen = set(eligible.tolist()); components = []
    while unseen:
        start = min(unseen); found = {start}; queue = deque([start]); unseen.remove(start)
        while queue:
            for other in graph[queue.popleft()]:
                if other in unseen:
                    unseen.remove(other); found.add(other); queue.append(other)
        components.append(np.array(sorted(found), dtype=np.int32))
    memberships = []
    for component in components:
        members = set(component.tolist())
        memberships.append({label: sorted(members & seed) for label, seed in seeds.items()})
    primary = {}
    for kind in ('outer', 'inner'):
        wanted = {kind+'0', kind+'7'}
        matches = [i for i, member in enumerate(memberships) if {label for label, ids in member.items() if ids} == wanted]
        assert len(matches) == 1, ('No unique through-band wall component', side, kind,
                                  [{label: len(ids) for label, ids in m.items()} for m in memberships])
        primary[kind] = matches[0]
    assert primary['outer'] != primary['inner']
    for kind, index in primary.items():
        for section in (0, 7):
            label = kind+str(section)
            expected = seeds[label] & set(eligible.tolist())
            assert set(memberships[index][label]) == expected, ('Split boundary seed ownership', side, label)
    assert sum(len(c) for c in components) == len(eligible)
    topology_rows = {kind: clipped_topology(xyz, faces, weld, scalar, components[index], lower, upper)
                     for kind, index in primary.items()}
    for kind, row in topology_rows.items():
        assert row['eulerCharacteristic'] == 0 and row['boundaryLoops'] == 2, ('Wall is not an annulus', side, kind, row)
        assert row['nonmanifoldEdges'] == 0 and row['inconsistentOrientedEdges'] == 0 and not row['badBoundaryVertexDegrees'], ('Wall manifold/orientation failure', side, kind, row)
        assert sorted(row['boundaryLoopCutPlanes']) == [[0], [1]], ('Wall boundary is not the two intended cuts', side, kind, row)
    report = {'side': side, 'lowerSourceAxialM': lower, 'upperSourceAxialM': upper,
              'method': 'Source oriented contour seeds at BOTH annulus planes, connected by exact-position-weld source face adjacency only where shared edges have positive length inside both axial cuts.',
              'nonmanifoldEdges': len(nonmanifold), 'wallTopology': topology_rows,
              'allEligibleFacesAccountedFor': True, 'excludedPositionDegenerateSourceFaces': excluded.tolist(),
              'outerComponent': primary['outer'], 'innerComponent': primary['inner'], 'components': []}
    for index, component in enumerate(components):
        points = np.unique(faces[component])
        report['components'].append({'index': index, 'sourceFaces': len(component), 'sourceVertices': len(points),
            'boundarySeedCounts': {label: len(ids) for label, ids in memberships[index].items()},
            'sourceAxialRangeM': [float(scalar[points].min()), float(scalar[points].max())],
            'ownership': next((kind for kind, i in primary.items() if i == index), 'additional-retained-unclassified')})
    payload = {f'{kind}SourceFaceIds': components[index] for kind, index in primary.items()}
    payload['excludedPositionDegenerateSourceFaceIds'] = excluded.astype(np.int32)
    payload['additionalSourceFaceIds'] = np.concatenate([c for i, c in enumerate(components) if i not in primary.values()]) if len(components) > 2 else np.empty(0, dtype=np.int32)
    for label, seed in seeds.items():
        payload[label+'SeedSourceFaceIds'] = np.array(sorted(seed), dtype=np.int32)
    return report, payload


def main():
    assert len(sys.argv) == 2
    out = Path(sys.argv[1]).resolve()
    assert out.is_relative_to(ROOT/'harness/out/rider-rebuild/astra-character-construction12') and not out.exists()
    config = json.loads((HERE/'input.json').read_text())
    prior = json.loads(pin(config['priorInputs']).read_text())
    helper = pin({'path': 'assets/blender/rider-rebuild/astra-character-construction12/inspect-source.py',
                  'sha256': 'f1f7c17b346d69bd5ac47252869464452c8d7918411890b5b4984bd2b9b38c69'})
    source, faces = runpy.run_path(str(helper))['read_source'](pin(prior['originalHoodie']))
    controls = json.loads(pin(prior['hoodieSourceFrames']).read_text())
    topology = json.loads(pin(config['sourceTopology']).read_text())
    result = {'acceptedArt': False, 'recipeSHA256': sha(Path(__file__)), 'source': prior['originalHoodie'],
              'topology': config['sourceTopology'], 'hands': {}}
    out.mkdir(parents=True)
    for side in ('L', 'R'):
        arrays = np.load(pin(topology['sides'][side]['arrays']))
        row, payload = band_ownership(source, faces, controls, topology, arrays, side)
        path = out/f'sleeve-{side}-ownership.npz'; np.savez_compressed(path, **payload)
        row['arrays'] = {'path': str(path.relative_to(ROOT)), 'sha256': sha(path)}
        result['hands'][side] = row
        (out/'ownership.json').write_text(json.dumps(result, indent=2)+'\n')
        print(json.dumps(row), flush=True)


if __name__ == '__main__':
    main()
