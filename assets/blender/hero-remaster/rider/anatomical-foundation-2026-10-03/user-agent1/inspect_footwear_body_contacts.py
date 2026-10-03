"""Measure upper AND outsole body contacts before moving wearable claims."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ap = argparse.ArgumentParser(description=__doc__); ap.add_argument('--source', required=True); ap.add_argument('--out', required=True)
a = ap.parse_args(sys.argv[sys.argv.index('--') + 1:]); source, output = Path(a.source).resolve(), Path(a.out).resolve()
bpy.ops.wm.open_mainfile(filepath=str(source)); body = bpy.data.objects['Canonical anatomical body, baked adult hm08']; boots = bpy.data.objects['Complete worn boot volume on own canonical feet']
body.data.calc_loop_triangles(); boots.data.calc_loop_triangles()
body_v = [v.co.copy() for v in body.data.vertices]; body_faces = [list(t.vertices) for t in body.data.loop_triangles]
tree = BVHTree.FromPolygons(body_v, body_faces, all_triangles=True); rows = []
for slot, name in [(0, 'upper'), (1, 'outsole')]:
    faces = [list(t.vertices) for t in boots.data.loop_triangles
        if (boots.data.polygons[t.polygon_index].material_index == 1) == (name == 'outsole')]
    own = BVHTree.FromPolygons([v.co.copy() for v in boots.data.vertices], faces, all_triangles=True); pairs = own.overlap(tree)
    rows.append({'part': name, 'triangles': len(faces), 'bodyTriangleContactPairs': len(pairs),
        'firstPairs': [{'partTriangle': i, 'partVertices': faces[i], 'bodyTriangle': j, 'bodyVertices': body_faces[j]} for i, j in pairs[:12]]})
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
report = {'status': 'REJECTED rest upper/outsole body intersection' if any(r['bodyTriangleContactPairs'] for r in rows) else 'UNACCEPTED rest upper and outsole body triangle proxy passes',
    'sourceMasterSHA256': sha(source), 'recipeSHA256': sha(__file__), 'parts': rows,
    'upperMaterialSlots': sorted({p.material_index for p in boots.data.polygons if p.material_index != 1}),
    'plantarAxisSeparationM': min(v.co.z for v in body.data.vertices) - max(boots.data.vertices[i].co.z for p in boots.data.polygons if p.material_index == 1 for i in p.vertices),
    'limits': ['Part/body triangle checks do not certify full signed clearance, collar motion or actual engine collision response.', 'Upper/outsole assembly overlap is intentional; body/outsole overlap is not dismissed as assembly.']}
output.write_text(json.dumps(report, indent=2)+'\n'); print(json.dumps(report))
