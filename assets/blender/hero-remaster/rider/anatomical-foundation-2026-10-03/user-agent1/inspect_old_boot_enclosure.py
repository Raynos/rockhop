"""Test old foot appearance volume numerically; do not infer holes from UV seams."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
import bpy
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ap = argparse.ArgumentParser(description=__doc__); ap.add_argument('--source', required=True); ap.add_argument('--out', required=True)
a = ap.parse_args(sys.argv[sys.argv.index('--') + 1:]); source, output = Path(a.source).resolve(), Path(a.out).resolve()
bpy.ops.wm.open_mainfile(filepath=str(source)); old = bpy.data.objects['Registered boots from bounded foot accessory regions']; body = bpy.data.objects['Canonical anatomical body, baked adult hm08']
bm = bmesh.new(); bm.from_mesh(old.data); bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-6)
boundaries = [e for e in bm.edges if len(e.link_faces) == 1]
cap = bmesh.ops.holes_fill(bm, edges=boundaries, sides=0)['faces']; bmesh.ops.triangulate(bm, faces=list(bm.faces)); bm.verts.ensure_lookup_table(); bm.verts.index_update()
vertices = [v.co.copy() for v in bm.verts]; faces = [[v.index for v in f.verts] for f in bm.faces]
tree = BVHTree.FromPolygons(vertices, faces, all_triangles=True)
def inside(point, direction):
    count = 0; p = point.copy()
    for _ in range(100):
        hit, normal, index, distance = tree.ray_cast(p, direction, 2.)
        if hit is None:
            return count % 2 == 1
        count += 1; p = hit + direction * 1e-6
    raise RuntimeError('Ambiguous closed-proxy ray; do not invent enclosure')
rows = []
for side, sign in [('L', -1), ('R', 1)]:
    selected = [v for v in body.data.vertices if v.co.z < .125 and v.co.y * sign > .075]
    outside = []
    for v in selected:
        votes = [inside(v.co, Vector(d)) for d in [(1, 0, 0), (0, 1, 0), (0, 0, 1)]]
        if sum(votes) < 2:
            outside.append({'bodyVertexID': v.index, 'restNativeM': list(v.co), 'insideVotes': votes})
    rows.append({'side': side, 'footBodyVerticesTestedBelowNativeZ': .125, 'verticesTested': len(selected), 'outsideMajorityRayProxy': len(outside), 'firstOutside': outside[:12]})
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
report = {'status': 'Old appearance boot rest enclosure diagnostic, not visual or moving acceptance', 'sourceMasterSHA256': sha(source), 'recipeSHA256': sha(__file__),
    'geometricWeldToleranceM': 1e-6, 'virtualCuffCapFaces': len(cap), 'closedProxyTriangles': len(faces), 'feet': rows,
    'limits': ['Old boots have two geometrically open ankle components; UV seam boundaries alone do not establish partial/missing upper volume.',
        'Virtual caps only support below125mm rest classification; old cuff is135.6..145mm. Three-axis majority ray parity is a proxy, not signed volume certification.',
        'Human played bare-forefoot/ankle and plastic-shoe verdict remains. Rest enclosure result must not override moving wear/appearance failure.']}
bm.free(); output.write_text(json.dumps(report, indent=2)+'\n'); print(json.dumps(report))
