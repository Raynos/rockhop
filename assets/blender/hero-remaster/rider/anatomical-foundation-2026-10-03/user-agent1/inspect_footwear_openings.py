"""Distinguish complete upper/sole topology from old appearance-fragment openings."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
import bpy
ap = argparse.ArgumentParser(description=__doc__); ap.add_argument('--source', required=True); ap.add_argument('--out', required=True)
a = ap.parse_args(sys.argv[sys.argv.index('--') + 1:]); source, output = Path(a.source).resolve(), Path(a.out).resolve()
bpy.ops.wm.open_mainfile(filepath=str(source))
def inspect(name):
    o = bpy.data.objects[name]; mesh = o.data; positions = [list(v.co) for v in mesh.vertices]
    # Geometric weld for reporting only; source/export is never changed.
    lookup = {}; vertex_map = []; welded = []
    for p in positions:
        key = tuple(round(x * 1e6) for x in p)
        if key not in lookup:
            lookup[key] = len(welded); welded.append(p)
        vertex_map.append(lookup[key])
    edges = {}; adjacency = {i: set() for i in range(len(welded))}
    for face in mesh.polygons:
        ids = [vertex_map[i] for i in face.vertices]
        for i, j in zip(ids, ids[1:] + ids[:1]):
            if i == j:
                continue
            edge = tuple(sorted((i, j))); edges[edge] = edges.get(edge, 0) + 1; adjacency[i].add(j); adjacency[j].add(i)
    remaining = set(adjacency); components = []
    while remaining:
        queue = [remaining.pop()]; used = set()
        while queue:
            i = queue.pop(); used.add(i); new = adjacency[i] & remaining; remaining -= new; queue.extend(new)
        boundary = [edge for edge, count in edges.items() if count == 1 and edge[0] in used]
        points = [welded[i] for edge in boundary for i in edge]
        components.append({'weldedVertices': len(used), 'boundaryEdges': len(boundary), 'overusedEdges': sum(count > 2 and edge[0] in used for edge, count in edges.items()),
            'boundaryNativeZRange': [min(p[2] for p in points), max(p[2] for p in points)] if points else None})
    return {'object': name, 'hiddenControl': o.hide_render, 'nativeVertices': len(positions), 'weldToleranceM': 1e-6, 'components': components}
old = inspect('Registered boots from bounded foot accessory regions'); new = inspect('Complete worn boot volume on own canonical feet')
assert len(new['components']) == 4 and all(c['overusedEdges'] == 0 for c in new['components'])
uppers = [c for c in new['components'] if c['boundaryEdges']]; soles = [c for c in new['components'] if not c['boundaryEdges']]
assert len(uppers) == len(soles) == 2 and all(max(abs(z-.165) for z in c['boundaryNativeZRange']) < 2e-6 for c in uppers)
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
report = {'status': 'UNACCEPTED complete upper/sole topology verified; moving footwear volume still needs review', 'sourceMasterSHA256': sha(source), 'recipeSHA256': sha(__file__),
    'oldAppearanceFragment': old, 'newCompleteFootwear': new, 'newUppersOpenOnlyAtAnklePlane': True, 'twoClosedGeometricSoles': True,
    'limits': ['Geometric weld is only a topology report, not an alteration to native or export data.', 'Ankle opening and closed soles distinguish constructed wear volume; they do not certify arbitrary-pose fit or final art.']}
output.write_text(json.dumps(report, indent=2)+'\n'); print(json.dumps(report))
