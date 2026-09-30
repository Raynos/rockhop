"""CPU surface retopology trial: dense rays, compact connected scalp, no bake.

Run with Blender background --python ... -- --input dense.npz --out trial1.
The cylindrical projection has explicit ear/undercut limitations. It is an
unaccepted first corrective trial, not production-ready character geometry.
"""
import argparse, hashlib, json, math, sys, time
from pathlib import Path
import bpy, bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--input', required=True); ap.add_argument('--out', required=True)
ap.add_argument('--angles', type=int, default=768)
ap.add_argument('--rows', type=int, default=640)
a = ap.parse_args(sys.argv[sys.argv.index('--') + 1:])
out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
if (out / 'head.glb').exists(): raise RuntimeError('Frozen trial exists')
def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''): h.update(b)
    return h.hexdigest()
before = sha(a.input); start = time.monotonic()
bpy.ops.wm.read_factory_settings(use_empty=True)
p = np.load(a.input); raw = p['vertices']; faces = p['faces']
# Work in canonical Blender (native X, -native Z, native Y).
v = raw[:, [0, 2, 1]].copy(); v[:, 1] *= -1
mesh = bpy.data.meshes.new('Untouched retained dense face target')
mesh.vertices.add(len(v)); mesh.vertices.foreach_set('co', v.ravel())
mesh.loops.add(faces.size); mesh.loops.foreach_set('vertex_index', faces.ravel())
mesh.polygons.add(len(faces))
mesh.polygons.foreach_set('loop_start', np.arange(len(faces), dtype=np.int32) * 3)
mesh.polygons.foreach_set('loop_total', np.full(len(faces), 3, dtype=np.int32))
mesh.update()
obj = bpy.data.objects.new('Dense target ONLY', mesh)
bpy.context.collection.objects.link(obj); bpy.context.view_layer.update()
bvh = BVHTree.FromObject(obj, bpy.context.evaluated_depsgraph_get())
print('Dense BVH ready', flush=True)
n, nr = a.angles, a.rows
theta = np.arange(n) * (2 * math.pi / n)
cs, sn = np.cos(theta), np.sin(theta)
ys = np.linspace(-.31, .365, nr, endpoint=False)
radius = np.zeros((nr, n), dtype=np.float64)
miss = 0
for j, y in enumerate(ys):
    for i in range(n):
        direction = Vector((float(sn[i]), float(-cs[i]), 0))
        origin = Vector((.8 * float(sn[i]), .025 - .8 * float(cs[i]), float(y)))
        hit, normal, idx, distance = bvh.ray_cast(origin, -direction, 1.6)
        if hit is None:
            radius[j, i] = np.nan; miss += 1
        else: radius[j, i] = .8 - distance
    if j % 80 == 0: print('Ray row', j, 'of', nr, flush=True)
# The controlled scalp ellipse replaces source curls; it is part of this mesh,
# sharing all ring vertices with retained face/neck projection, never a shell.
height = np.where(cs >= 0, .13 + .10 * cs, .13 + .25 * cs)
elliptical = np.sqrt(np.maximum(0, 1 - ((ys[:, None] - .04) / .325) ** 2))
radial_xy = 1 / np.sqrt((sn / .215) ** 2 + (cs / .245) ** 2)
scalp = elliptical * radial_xy[None, :]
blend = np.clip((ys[:, None] - height[None, :] + .018) / .045, 0, 1)
blend = blend * blend * (3 - 2 * blend)
source_missing_outside_scalp = int(np.sum(~np.isfinite(radius) & (blend < .999)))
radius = np.where(np.isfinite(radius), radius, scalp)
radius = radius * (1 - blend) + scalp * blend
# Local beard smoothing only, no whole-head voxel operation or global remesh.
# Native beard area: below lower lip, front half. Preserve nose/lip samples.
beard = ((ys[:, None] > -.145) & (ys[:, None] < -.025) &
         (cs[None, :] > .15)).astype(float)
kernel = np.array([1, 4, 6, 4, 1], dtype=float) / 16
smooth = sum(w * np.roll(radius, shift, axis=1)
             for shift, w in zip(range(-2, 3), kernel))
pad = np.pad(smooth, ((2, 2), (0, 0)), mode='edge')
smooth = sum(w * pad[2+shift:2+shift+nr]
             for shift, w in zip(range(-2, 3), kernel))
radius = radius * (1 - beard) + smooth * beard
grid = np.stack((radius * sn, .025 - radius * cs,
                 np.broadcast_to(ys[:, None], radius.shape)), axis=-1)
verts = grid.reshape(-1, 3)
ids = np.arange(nr*n).reshape(nr, n)
a0 = ids[:-1].ravel(); b0 = np.roll(ids[:-1], -1, axis=1).ravel()
c0 = ids[1:].ravel(); d0 = np.roll(ids[1:], -1, axis=1).ravel()
tri = np.concatenate((np.stack((a0, b0, c0), axis=1),
                      np.stack((b0, d0, c0), axis=1)))
apex = len(verts); verts = np.vstack((verts, [0, .025, .365]))
tri = np.vstack((tri, np.stack((ids[-1], np.roll(ids[-1], -1),
                              np.full(n, apex)), axis=1)))
clean_mesh = bpy.data.meshes.new('Connected retopology first trial')
clean_mesh.from_pydata(verts.tolist(), [], tri.tolist()); clean_mesh.update()
clean = bpy.data.objects.new('UNACCEPTED dense-projected compact head', clean_mesh)
bpy.context.collection.objects.link(clean)
bpy.context.view_layer.objects.active = clean; clean.select_set(True)
bm = bmesh.new(); bm.from_mesh(clean_mesh)
bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
bm.to_mesh(clean_mesh); bm.free()
for polygon in clean_mesh.polygons: polygon.use_smooth = True
bpy.data.objects.remove(obj, do_unlink=True); bpy.data.meshes.remove(mesh)
mat = bpy.data.materials.new('Gray inspection only'); mat.use_nodes = True
bsdf = mat.node_tree.nodes.get('Principled BSDF')
bsdf.inputs['Base Color'].default_value = (.42, .42, .42, 1)
bsdf.inputs['Roughness'].default_value = .65; clean.data.materials.append(mat)
bpy.ops.wm.save_as_mainfile(filepath=str(out / 'head.blend'))
bpy.ops.export_scene.gltf(filepath=str(out / 'head.glb'), export_format='GLB',
                          use_selection=True, export_yup=True)
# Exact construction arrays, native coordinate adapter for parent integration.
native = verts[:, [0, 2, 1]].copy(); native[:, 2] *= -1
np.savez(out / 'head.npz', vertices=native.astype(np.float32),
         faces=tri.astype(np.int32), scalp_blend=blend.astype(np.float32),
         source_projected_radius=radius.astype(np.float32))
report = dict(status='UNACCEPTED first corrective trial; gray review before bake',
              source=a.input, sourceSHA256=before, sourceSHA256After=sha(a.input),
              scriptSHA256=sha(__file__), blender=bpy.app.version_string,
              vertices=len(verts), faces=len(tri), angles=n, rows=nr,
              raysMissed=miss, raysMissingOutsideScalp=source_missing_outside_scalp,
              method='dense BVH outer surface projection + continuous analytic scalp',
              scalp=dict(xRadius=.215, zRadius=.245, yRadius=.325,
                         centerNativeY=.04, centerNativeZ=-.025),
              boundaryEdges=n, nonmanifoldEdges=0,
              openBoundary='single base loop at nativeY=-.31, for body join',
              wallSeconds=time.monotonic()-start,
              limits=['Cylindrical projection cannot preserve folded ear undercuts.',
                      'Missing non-scalp rays require visual review; no inferred pass.',
                      'Face surface sampled at finite grid resolution, not untouched triangles.',
                      'No UVs/detail/PBR bake, rig, neck join, or game readiness.'])
assert report['sourceSHA256After'] == before
(out / 'construction.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report), flush=True)
