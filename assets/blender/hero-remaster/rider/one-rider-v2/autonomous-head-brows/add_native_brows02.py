"""Fit installed CC0 brows to the unchanged evaluated native head, CPU only."""
import hashlib
import json
from pathlib import Path
import bpy
import addon_utils
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path('/Users/raynos/projects/games/rockhop')
RUN = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
OUT = RUN / 'autonomous-head-brows/trial02'
EVIDENCE = ROOT / 'docs/evidence/hero-remaster/one-rider-v2/autonomous-head-brows/trial01'
OUT.mkdir(parents=True, exist_ok=True)
EVIDENCE.mkdir(parents=True, exist_ok=True)
if (OUT / 'head.blend').exists():
    raise RuntimeError('Frozen result exists; do not overwrite')
SOURCE = RUN / 'head-cleanup/mpfb-v6-native-male/fresh-native-source.blend'
HEAD = RUN / 'head-cleanup/mpfb-v8-palette/african/head.blend'
ASSET = Path('/Users/raynos/Library/Application Support/Blender/5.1/extensions/.user/user_default/mpfb/data/eyebrows/eyebrow001/eyebrow001.mhclo')
ADDON = Path('/Users/raynos/Library/Application Support/Blender/5.1/extensions/user_default')

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

sources = {str(p): sha(p) for p in [SOURCE, HEAD, ASSET, ASSET.with_suffix('.obj'), ASSET.with_suffix('.mhmat'), ASSET.with_suffix('.png')]}
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.preferences.extensions.repos.new(name='Owned native brow fit', module='owned_brows_mpfb', custom_directory=str(ADDON))
addon_utils.enable('bl_ext.owned_brows_mpfb.mpfb', default_set=True, persistent=False)
from bl_ext.owned_brows_mpfb.mpfb.services.humanservice import HumanService
from bl_ext.owned_brows_mpfb.mpfb.services.targetservice import TargetService
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
body = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
TargetService.bake_targets(body)
brows = HumanService.add_mhclo_asset(str(ASSET), body, asset_type='Eyebrows', subdiv_levels=0,
    set_up_rigging=False, interpolate_weights=False, import_subrig=False, import_weights=False)
if brows.data.shape_keys:
    TargetService.bake_targets(brows)
construction = json.loads((RUN / 'head-cleanup/mpfb-v6-native-male/construction.json').read_text())
adapter = construction['adapter']
scale = adapter['uniformScale']
ty = adapter['verticalTranslation']
tz = adapter['depthTranslation']
matrix = brows.matrix_world.copy()
positions = []
for vertex in brows.data.vertices:
    p = matrix @ vertex.co
    positions.append((scale * p.x, scale * p.y - tz, scale * p.z + ty))
polygons = [list(p.vertices) for p in brows.data.polygons]
uvs = [list(loop.uv) for loop in brows.data.uv_layers.active.data]
bpy.ops.wm.open_mainfile(filepath=str(HEAD))

def geometry_proof():
    data = {o.name: {'vertices': [list(v.co) for v in o.data.vertices],
        'faces': [list(p.vertices) for p in o.data.polygons],
        'uv': [[list(t.uv) for t in layer.data] for layer in o.data.uv_layers]}
        for o in bpy.context.scene.objects if o.type == 'MESH'}
    return hashlib.sha256(json.dumps(data, separators=(',', ':')).encode()).hexdigest()

before = geometry_proof()
skin = max((o for o in bpy.context.scene.objects if o.type == 'MESH'), key=lambda o: len(o.data.vertices))
bvh = BVHTree.FromPolygons([v.co for v in skin.data.vertices], [p.vertices for p in skin.data.polygons], all_triangles=False)
fitted = []
distances = []
for p in positions:
    point, normal, _, distance = bvh.find_nearest(Vector(p))
    if point is None or distance > .015:
        raise RuntimeError('Native brow fit farther than15mm native; freeze before any projection')
    fitted.append(tuple(point + normal * .0006))
    distances.append(distance)
mesh = bpy.data.meshes.new('CC0 brow001 native-fit surface')
mesh.from_pydata(fitted, [], polygons)
mesh.update()
layer = mesh.uv_layers.new(name='NativeBrowUV')
for target, value in zip(layer.data, uvs):
    target.uv = value
obj = bpy.data.objects.new('NEW CC0 native eyebrow001', mesh)
bpy.context.scene.collection.objects.link(obj)
for polygon in mesh.polygons:
    polygon.use_smooth = True
mat = bpy.data.materials.new('CC0 eyebrow001 diffuse alpha')
mat.use_nodes = True
nodes = mat.node_tree.nodes
links = mat.node_tree.links
shader = nodes.get('Principled BSDF')
shader.inputs['Metallic'].default_value = 0
shader.inputs['Roughness'].default_value = .8
texture = nodes.new('ShaderNodeTexImage')
texture.image = bpy.data.images.load(str(ASSET.with_suffix('.png')), check_existing=False)
texture.image.pack()
links.new(texture.outputs['Color'], shader.inputs['Base Color'])
links.new(texture.outputs['Alpha'], shader.inputs['Alpha'])
if hasattr(mat, 'surface_render_method'):
    mat.surface_render_method = 'DITHERED'
mesh.materials.append(mat)
# Prove the original native face/eyes stayed exact; omit only the new brow object.
bpy.data.objects.remove(obj, do_unlink=True)
after = geometry_proof()
assert before == after
bpy.context.scene.collection.objects.link(bpy.data.objects.new('NEW CC0 native eyebrow001', mesh))
bpy.ops.object.select_all(action='SELECT')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'head.blend'))
bpy.ops.export_scene.gltf(filepath=str(OUT / 'head.glb'), export_format='GLB', use_selection=True,
    export_animations=False, export_yup=True)
assert sources == {path: sha(path) for path in sources}
(EVIDENCE / 'construction.json').write_text(json.dumps({
    'status': 'UNACCEPTED native eyebrow fit; parent actual PBR review required',
    'sources': sources, 'sourcesAfter': {path: sha(path) for path in sources},
    'Blender': bpy.app.version_string, 'nativeUniformAdapter': adapter,
    'headEyeGeometryUVSHA256Before': before, 'headEyeGeometryUVSHA256After': after,
    'browVertices': len(fitted), 'browPolygons': len(polygons),
    'maximumSourceToSubdivisionSkinFitNativeM': max(distances),
    'newBrowSurfaceOffsetNativeM': .0006, 'headGeometryChanged': False,
    'headMasterSHA256': sha(OUT / 'head.blend'), 'headGLBSHA256': sha(OUT / 'head.glb'),
    'assetLicence': 'Installed mhclo/mhmat declare CC0 September2020; original files hashed',
    'limits': ['Native skin diffuse only; no highpoly texture bake or exact likeness claim',
        'Eyebrow surface fitted to unchanged skin; no accepted whole rider, neck join or rig']
}, indent=2) + '\n')
