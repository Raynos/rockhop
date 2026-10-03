"""Unchanged standing mesh with candidate seam cycles; review only."""
from pathlib import Path
import json, math
ROOT = Path('/Users/raynos/projects/games/rockhop/assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3')
setup = (ROOT/'scripts/render_stills.py').read_text().split('cases=sys.argv')[0]
setup = setup.replace('root=Path.cwd()', 'root=ROOT').replace("root/'baseline/rider.glb'", "ROOT/'deliverables/C19.glb'")
exec(compile(setup, 'render_stills.py', 'exec'))
CC = np.array([[1,0,0],[0,0,-1],[0,1,0]])
normal = np.concatenate([g.array(p['attributes']['NORMAL']) for p in prims]) @ CC.T
for ob, ix in zip(meshes, maps):
    ob.data.vertices.foreach_set('co', (r @ CC.T)[ix].astype('f4').ravel())
    ob.data.update()
    ob.data.normals_split_custom_set_from_vertices(normal[ix].tolist())
for ob in bikeobjects:
    ob.hide_render = True
for label, color in [('geometry', (.03,.8,.95)), ('texture-clues', (.95,.03,.38))]:
    source = np.load(ROOT/'hoodie-repair03/lower-foundation/seam-proposals'/f'{label}.npz')
    points = source['sourcePoints'][source['cycle']] @ CC.T
    # Display the actual curve without moving any rider vertices. Tube radius
    # is explicit; no face masking, geometry clipping or repair is performed.
    curve = bpy.data.curves.new(label, 'CURVE')
    curve.dimensions = '3D'; curve.bevel_depth = .0012; curve.bevel_resolution = 2
    spline = curve.splines.new('POLY'); spline.points.add(len(points)-1)
    for point, xyz in zip(spline.points, points):
        point.co = (*xyz, 1)
    spline.use_cyclic_u = True
    obj = bpy.data.objects.new(label, curve); sc.collection.objects.link(obj)
    m = mat(label, color)
    m.node_tree.nodes['Principled BSDF'].inputs['Emission Color'].default_value = (*color,1)
    m.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 1.5
    obj.data.materials.append(m)
original = {ob:list(ob.data.materials) for ob in meshes}
gray = mat('source geometry', (.42,.42,.42))
d.type = 'ORTHO'; d.ortho_scale = .52
sc.render.resolution_x = sc.render.resolution_y = 640; sc.cycles.samples = 6
out = ROOT/'hoodie-repair03/lower-foundation/seam-proposals/renders'; out.mkdir(exist_ok=True)
target = Vector((.63,0,.982))
for view, angle in [('front',0),('side',90),('back',180)]:
    cam.location = target + Vector((4*math.cos(math.radians(angle)),4*math.sin(math.radians(angle)),0))
    cam.rotation_euler = (target-cam.location).to_track_quat('-Z','Y').to_euler()
    for appearance in ['pbr','gray']:
        for ob in meshes:
            for i in range(len(ob.data.materials)):
                ob.data.materials[i] = gray if appearance=='gray' else original[ob][i]
        sc.render.filepath = str(out/f'{view}-{appearance}.png'); bpy.ops.render.render(write_still=True)
print('UNCHANGED LOWER SOURCE / DIAGNOSTIC SEAM OVERLAYS COMPLETE')
