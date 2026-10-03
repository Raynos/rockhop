"""Assemble protected appearance on the clean own-bind corrective foundation.

This is a frozen UNACCEPTED look-development candidate, not player promotion.
Donor body serves only as a registered colour-sampling surface. Face above
neck interface and its UV/image bytes are preserved; accessories are re-bound.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import bpy
import bmesh
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

ap = argparse.ArgumentParser(description=__doc__)
for name in ['source', 'donor', 'registration', 'images', 'out', 'evidence']:
    ap.add_argument('--' + name, required=True)
a = ap.parse_args(sys.argv[sys.argv.index('--') + 1:])
source, donor, registration, images, out, evidence = [Path(getattr(a, n)).resolve() for n in ['source', 'donor', 'registration', 'images', 'out', 'evidence']]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(donor) == 'b7f4f22790124c664f9907104e5b17b77775b4c5c995f715d62be640bbcc8754'
assert sha(source) == 'bc09459896daacaba778cd73fd63afec25b632b5197dd5376199584839121237'
out.mkdir(parents=True, exist_ok=True); evidence.mkdir(parents=True, exist_ok=True)
if (out / 'rider.blend').exists():
    raise RuntimeError('Frozen assembly exists; use a new reviewed leaf')
pins = {str(p): sha(p) for p in [source, donor, registration]}
bpy.ops.wm.open_mainfile(filepath=str(source))
rig = bpy.data.objects['Independent anatomical foundation rig']
root = bpy.data.objects['Foundation file frame, game x0.65']
body = bpy.data.objects['Canonical anatomical body, baked adult hm08']
shirt = bpy.data.objects['Separate fitted sweatshirt control, hood not constructed']
jeans = bpy.data.objects['Separate fitted native trousers control']
for pb in rig.pose.bones:
    pb.location = (0, 0, 0); pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = (1, 0, 0, 0); pb.scale = (1, 1, 1)
for o in [shirt, jeans]:
    for key in o.data.shape_keys.key_blocks:
        key.value = 0
bpy.context.view_layer.update()
raw = donor.read_bytes(); length = int.from_bytes(raw[12:16], 'little')
doc = json.loads(raw[20:20 + length]); binary = raw[28 + length:]
record = json.loads(registration.read_text())

def acc(index):
    aa = doc['accessors'][index]; vv = doc['bufferViews'][aa['bufferView']]
    nc = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}[aa['type']]
    dt = np.dtype({5126: '<f4', 5125: '<u4', 5123: '<u2', 5121: '<u1'}[aa['componentType']])
    return np.ndarray((aa['count'], nc), dtype=dt, buffer=binary,
        offset=vv.get('byteOffset', 0) + aa.get('byteOffset', 0), strides=(vv.get('byteStride', nc * dt.itemsize), dt.itemsize)).copy()

C = np.array([[1., 0, 0, -.65], [0, 0, -1, 0], [0, 1, 0, 0], [0, 0, 0, 1]])
role = lambda n: n if n.endswith(('.L', '.R')) else n[:-1] + '.' + n[-1] if n[-1:] in ['L', 'R'] else n
joint_names = [doc['nodes'][i]['name'] for i in doc['skins'][0]['joints']]
source_bones = {j['id']: C @ np.array(j['matrixWorld']).reshape(4, 4).T for j in record['rows'][0]['joints']}
# Some joints absent in primitive0 remain registered in other primitives.
for row in record['rows']:
    for j in row['joints']:
        source_bones[j['id']] = C @ np.array(j['matrixWorld']).reshape(4, 4).T
# Missing zero-mass roles (neck/head/shoulders) still require exact old rest
# frames. Evaluate original node hierarchy read-only rather than invent frames.
node_world = {}
parents = {child: parent for parent, node in enumerate(doc['nodes']) for child in node.get('children', [])}
def world(index):
    if index in node_world:
        return node_world[index]
    node = doc['nodes'][index]
    if 'matrix' in node:
        local = Matrix(np.array(node['matrix']).reshape(4, 4).T.tolist())
    else:
        from mathutils import Quaternion
        q = node.get('rotation', [0, 0, 0, 1]); quat = Quaternion((q[3], q[0], q[1], q[2]))
        local = Matrix.LocRotScale(Vector(node.get('translation', [0, 0, 0])), quat, Vector(node.get('scale', [1, 1, 1])))
    node_world[index] = world(parents[index]) @ local if index in parents else local
    return node_world[index]
for i, node in enumerate(doc['skins'][0]['joints']):
    source_bones.setdefault(i, C @ np.array(world(node)))
maps = {i: np.array(rig.data.bones[role(n)].matrix_local) @ np.linalg.inv(source_bones[i]) for i, n in enumerate(joint_names)}

materials = {}
loaded = {}
def image(index):
    if index not in loaded:
        loaded[index] = bpy.data.images.load(str(images / f'donor-image-{index}.png'), check_existing=False)
        loaded[index].name = f'Protected donor exact image {index}'
        loaded[index].pack()
    return loaded[index]

def mat(index):
    if index in materials:
        return materials[index]
    spec = doc['materials'][index]; pbr = spec['pbrMetallicRoughness']
    m = bpy.data.materials.new(f'Appearance exact donor material {index}'); m.use_nodes = True
    nt = m.node_tree; bs = nt.nodes.get('Principled BSDF')
    bs.inputs['Metallic'].default_value = pbr.get('metallicFactor', 1)
    bs.inputs['Roughness'].default_value = pbr.get('roughnessFactor', 1)
    bs.inputs['Specular IOR Level'].default_value = spec.get('extensions', {}).get('KHR_materials_specular', {}).get('specularFactor', .25)
    def texture(tex, noncolour=False):
        node = nt.nodes.new('ShaderNodeTexImage'); node.image = image(doc['textures'][tex['index']]['source'])
        if noncolour:
            node.image.colorspace_settings.name = 'Non-Color'
        uv = nt.nodes.new('ShaderNodeUVMap'); uv.uv_map = 'UVMap.001' if tex.get('texCoord', 0) == 1 else 'UVMap'
        nt.links.new(uv.outputs['UV'], node.inputs['Vector']); return node
    if 'baseColorTexture' in pbr:
        node = texture(pbr['baseColorTexture']); nt.links.new(node.outputs['Color'], bs.inputs['Base Color'])
    if 'normalTexture' in spec:
        node = texture(spec['normalTexture'], True); normal = nt.nodes.new('ShaderNodeNormalMap')
        normal.uv_map = 'UVMap.001'; nt.links.new(node.outputs['Color'], normal.inputs['Color']); nt.links.new(normal.outputs[0], bs.inputs['Normal'])
    if 'metallicRoughnessTexture' in pbr:
        node = texture(pbr['metallicRoughnessTexture'], True); sep = nt.nodes.new('ShaderNodeSeparateColor')
        nt.links.new(node.outputs['Color'], sep.inputs['Color']); nt.links.new(sep.outputs['Green'], bs.inputs['Roughness']); nt.links.new(sep.outputs['Blue'], bs.inputs['Metallic'])
    materials[index] = m; return m

body.data.calc_loop_triangles()
body_vertices = np.array([v.co[:] for v in body.data.vertices])
body_faces = np.array([t.vertices[:] for t in body.data.loop_triangles])
body_tree = BVHTree.FromPolygons([Vector(v) for v in body_vertices], body_faces.tolist(), all_triangles=True)
body_weights = [{body.vertex_groups[g.group].name: g.weight for g in v.groups if g.weight > 0 and body.vertex_groups[g.group].name in rig.data.bones} for v in body.data.vertices]


def bary(p, tri):
    v0, v1, v2 = tri[1] - tri[0], tri[2] - tri[0], p - tri[0]
    aa, bb, cc, dd, ee = np.dot(v0, v0), np.dot(v0, v1), np.dot(v1, v1), np.dot(v2, v0), np.dot(v2, v1)
    den = aa * cc - bb * bb
    if abs(den) < 1e-18:
        return np.array([1., 0, 0])
    y, z = (cc * dd - bb * ee) / den, (aa * ee - bb * dd) / den
    result = np.clip([1 - y - z, y, z], 0, 1); return result / sum(result)


def weight_near(point):
    q, normal, tri, distance = body_tree.find_nearest(Vector(point))
    ids = body_faces[tri]; factors = bary(np.array(q), body_vertices[ids]); w = {}
    for i, factor in zip(ids, factors):
        for name, value in body_weights[i].items():
            w[name] = w.get(name, 0) + value * factor
    w = sorted(w.items(), key=lambda p: -p[1])[:4]; total = sum(x[1] for x in w)
    return [(name, value / total) for name, value in w], distance


def primitive(mi, pi, map_rest=False):
    p = doc['meshes'][mi]['primitives'][pi]; attr = {k: acc(v) for k, v in p['attributes'].items()}
    points = np.column_stack([attr['POSITION'], np.ones(len(attr['POSITION']))]) @ C.T
    if map_rest:
        registered = np.zeros_like(points)
        for k in range(4):
            for j in np.unique(attr['JOINTS_0'][:, k]):
                mask = attr['JOINTS_0'][:, k] == j
                registered[mask] += (points[mask] @ maps[int(j)].T) * attr['WEIGHTS_0'][mask, k:k+1]
        points = registered
    return p, attr, points[:, :3], acc(p['indices']).reshape(-1, 3)

objects = []; construction = []
def create(mi, pi, label, map_rest=False, select=None, nearest_weights=False, material_override=None):
    p, attrs, points, triangles = primitive(mi, pi, map_rest)
    valid = np.ones(len(points), dtype=bool) if select is None else select(points, attrs)
    triangles = triangles[np.all(valid[triangles], axis=1)]
    used = np.unique(triangles); inverse = np.full(len(points), -1); inverse[used] = np.arange(len(used))
    mesh = bpy.data.meshes.new(label); mesh.from_pydata(points[used].tolist(), [], inverse[triangles].tolist()); mesh.update()
    o = bpy.data.objects.new(label, mesh); bpy.context.collection.objects.link(o); o.parent = root
    mesh.materials.append(mat(p['material']) if material_override is None else material_override)
    for channel in [0, 1]:
        name = f'TEXCOORD_{channel}'
        if name not in attrs:
            continue
        layer = mesh.uv_layers.new(name='UVMap' if channel == 0 else 'UVMap.001')
        for loop in mesh.loops:
            uv = attrs[name][used[loop.vertex_index]]; layer.data[loop.index].uv = (float(uv[0]), 1 - float(uv[1]))
    for b in rig.data.bones:
        o.vertex_groups.new(name=b.name)
    maximum_distance = 0
    for i, old in enumerate(used):
        if nearest_weights:
            weights, distance = weight_near(points[old]); maximum_distance = max(maximum_distance, distance)
        else:
            weights = [(role(joint_names[int(j)]), float(w)) for j, w in zip(attrs['JOINTS_0'][old], attrs['WEIGHTS_0'][old]) if w > 0]
        for name, w in weights:
            o.vertex_groups[name].add([i], w, 'REPLACE')
    mod = o.modifiers.new('Own 51-joint bind', 'ARMATURE'); mod.object = rig
    for f in mesh.polygons:
        f.use_smooth = True
    objects.append(o)
    row = {'name': label, 'sourceMesh': mi, 'primitive': pi, 'vertices': len(used), 'triangles': len(triangles),
        'sourceVertexIDsSHA256': hashlib.sha256(used.astype('<u4').tobytes()).hexdigest(), 'registration': 'own rest bone frames' if map_rest else 'protected original file-world rest',
        'binding': 'nearest canonical surface barycentric own top4' if nearest_weights else 'semantic weights rebound to own joints, no old bind matrices',
        'maximumCanonicalWeightTransferDistanceM': maximum_distance,
        'boundsNativeM': [points[used].min(0).tolist(), points[used].max(0).tolist()]}
    construction.append(row); print('ASSEMBLED_PART', row, flush=True); return o

# Protected face/hair pixels and vertices above the hidden collar cut are unchanged.
head = create(1, 0, 'Protected textured head above hidden neck interface', select=lambda p, a: p[:, 2] >= 1.525)
cheek = create(1, 1, 'Protected coherent cheek patch', select=lambda p, a: p[:, 2] >= 1.525)
# Retain original canonical body in master; export an explicit head-interface derivative.
visible_body = body.copy(); visible_body.data = body.data.copy(); visible_body.name = 'Canonical body with hidden head interface'; bpy.context.collection.objects.link(visible_body)
bm = bmesh.new(); bm.from_mesh(visible_body.data); remove = [v for v in bm.verts if v.co.z > 1.54]
bmesh.ops.delete(bm, geom=remove, context='VERTS'); bm.to_mesh(visible_body.data); bm.free()
body.hide_render = True
skin = bpy.data.materials.new('Canonical skin paired with protected head'); skin.use_nodes = True
skin.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.46, .245, .155, 1)
skin.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = .65
visible_body.data.materials.clear(); visible_body.data.materials.append(skin)
objects.append(visible_body)
hood = create(0, 2, 'Protected mustard hood on own rig', nearest_weights=True)
gloves = create(0, 1, 'Registered black leather gloves on own finger bind', map_rest=True, nearest_weights=True)
# Boots are bounded accessory regions, not an adoption of the fused donor body.
boots = create(0, 0, 'Registered boots from bounded foot accessory regions', map_rest=True,
    select=lambda p, a: np.sum(a['WEIGHTS_0'] * np.isin(a['JOINTS_0'], [next(i for i, n in enumerate(joint_names) if role(n) == 'foot.L'), next(i for i, n in enumerate(joint_names) if role(n) == 'foot.R')]), axis=1) >= .45,
    nearest_weights=True, material_override=mat(1))
# Boots reuse material1 leather with UV0 coordinates copied explicitly to UV1.
for i, item in enumerate(boots.data.uv_layers['UVMap'].data):
    boots.data.uv_layers['UVMap.001'].data[i].uv = item.uv

# Map the donor clothing surface into own-rest frames only for texture donation.
p, attrs, donor_points, donor_faces = primitive(0, 0, True)
source_image = image(0); ww, hh = source_image.size
source_pixels = np.array(source_image.pixels[:], dtype=np.float32).reshape(hh, ww, 4)
source_uv = attrs['TEXCOORD_0'].copy(); source_uv[:, 1] = 1 - source_uv[:, 1]
texture_rows = []
for garment, label, fallback in [(shirt, 'mustard-hoodie', [.73, .49, .20, 1]), (jeans, 'indigo-jeans', [.15, .22, .32, 1])]:
    garment.data.calc_loop_triangles(); uv_layer = garment.data.uv_layers.active
    if garment == shirt:
        allowed = np.isin(attrs['JOINTS_0'][np.arange(len(donor_points)), attrs['WEIGHTS_0'].argmax(1)],
            [next(i for i, name in enumerate(joint_names) if role(name) == role(n)) for n in ['chest', 'spine', 'pelvis', 'shoulderL', 'shoulderR', 'upperArmL', 'upperArmR', 'forearmL', 'forearmR']])
    else:
        allowed = np.isin(attrs['JOINTS_0'][np.arange(len(donor_points)), attrs['WEIGHTS_0'].argmax(1)],
            [next(i for i, name in enumerate(joint_names) if role(name) == role(n)) for n in ['pelvis', 'thighL', 'thighR', 'shinL', 'shinR']])
    faces = donor_faces[np.all(allowed[donor_faces], axis=1)]
    tree = BVHTree.FromPolygons([Vector(v) for v in donor_points], faces.tolist(), all_triangles=True)
    size = 512; pixels = np.tile(np.array(fallback, dtype=np.float32), (size, size, 1)); painted = np.zeros((size, size), bool)
    distances = []
    for tri in garment.data.loop_triangles:
        uvs = np.array([uv_layer.data[i].uv[:] for i in tri.loops]) * (size - 1)
        coords = np.array([garment.data.vertices[i].co[:] for i in tri.vertices])
        lower = np.maximum(0, np.floor(uvs.min(0)).astype(int)); upper = np.minimum(size - 1, np.ceil(uvs.max(0)).astype(int))
        uvtri = np.column_stack([uvs, np.zeros(3)])
        v0, v1 = uvs[1] - uvs[0], uvs[2] - uvs[0]; den = v0[0] * v1[1] - v1[0] * v0[1]
        if abs(den) < 1e-8:
            continue
        for yy in range(lower[1], upper[1] + 1):
            for xx in range(lower[0], upper[0] + 1):
                v2 = np.array([xx, yy]) - uvs[0]
                b, c = (v2[0] * v1[1] - v1[0] * v2[1]) / den, (v0[0] * v2[1] - v2[0] * v0[1]) / den
                weights = np.array([1 - b - c, b, c])
                if weights.min() < -1e-6:
                    continue
                point = weights @ coords; q, normal, face, distance = tree.find_nearest(Vector(point))
                ids = faces[face]; uv = bary(np.array(q), donor_points[ids]) @ source_uv[ids]
                sx = min(ww - 1, max(0, round(float(uv[0]) * (ww - 1)))); sy = min(hh - 1, max(0, round(float(uv[1]) * (hh - 1))))
                colour = source_pixels[sy, sx].copy()
                # Atlas joint regions overlap at pelvis; reject cross-garment hue.
                if (garment == shirt and not (colour[0] > colour[2] * 1.4 and colour[0] > colour[1] * 1.15)) or (garment == jeans and colour[2] < colour[0] * 1.05):
                    colour = np.array(fallback, dtype=np.float32)
                pixels[yy, xx] = colour; painted[yy, xx] = True; distances.append(distance)
    # Four-pixel dilation fills UV gutters without changing any UV/geometry.
    for step in range(4):
        old = painted.copy()
        for axis, amount in [(0, 1), (0, -1), (1, 1), (1, -1)]:
            neighbors = np.roll(old, amount, axis); mask = ~painted & neighbors
            pixels[mask] = np.roll(pixels, amount, axis)[mask]; painted[mask] = True
    tex = bpy.data.images.new('Transferred approved ' + label + ' atlas', width=size, height=size, alpha=True)
    tex.pixels.foreach_set(pixels.ravel()); tex.filepath_raw = str(out / (label + '-albedo.png')); tex.file_format = 'PNG'; tex.save(); tex.pack()
    m = bpy.data.materials.new('Transferred approved ' + label + ' PBR'); m.use_nodes = True
    nt = m.node_tree; bs = nt.nodes['Principled BSDF']; bs.inputs['Roughness'].default_value = .75; bs.inputs['Metallic'].default_value = 0
    bs.inputs['Specular IOR Level'].default_value = .25
    node = nt.nodes.new('ShaderNodeTexImage'); node.image = tex; nt.links.new(node.outputs['Color'], bs.inputs['Base Color'])
    garment.data.materials.clear(); garment.data.materials.append(m)
    texture_rows.append({'garment': garment.name, 'file': str(Path(tex.filepath_raw)), 'sha256': sha(tex.filepath_raw),
        'size': [size, size], 'coveredPixelsIncludingGutter': int(painted.sum()), 'registeredDonationDistanceP95M': float(np.quantile(distances, .95)),
        'limitations': 'Surface-correspondence colour donation with hue guard at mixed pelvis atlas; original garment UV/topology/weights/keys remain unchanged'})
    print('TRANSFERRED_TEXTURE', texture_rows[-1], flush=True)

shirt['appearanceCandidate'] = 'unaccepted appearance01'; jeans['appearanceCandidate'] = 'unaccepted appearance01'
root['rockhopRiderSkinConditioned'] = 1; root['rockhopAppearanceCandidate'] = 'unaccepted appearance01'
for o in bpy.data.objects:
    if o.type == 'MESH':
        o.hide_render = o not in objects + [shirt, jeans]
bpy.ops.object.select_all(action='DESELECT')
for o in [root, rig, shirt, jeans] + objects:
    o.hide_set(False); o.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.wm.save_as_mainfile(filepath=str(out / 'rider.blend'), compress=True)
bpy.ops.export_scene.gltf(filepath=str(out / 'rider.glb'), export_format='GLB', use_selection=True,
    export_yup=True, export_animations=False, export_attributes=True, export_extras=True, export_morph=True)
assert pins == {str(p): sha(p) for p in [source, donor, registration]}
report = {'status': 'UNACCEPTED recognizable textured own-bind appearance assembly; moving review and fit qualification pending',
    'pins': pins, 'recipeSHA256': sha(__file__), 'masterSHA256': sha(out / 'rider.blend'), 'GLBSHA256': sha(out / 'rider.glb'),
    'joints': [b.name for b in rig.data.bones if b.use_deform], 'parts': construction, 'transferredTextures': texture_rows,
    'limits': ['Protected head vertices/UV/PBR above z1.525m are preserved; hidden collar/bust interface deliberately cropped.',
        'Canonical body preserved hidden in native master; visible derivative removes native head above1.54m only.',
        'Native sweatshirt/jeans basis, UV, weights and liked local correctives remain; no fused donor body adoption.',
        'Hood/accessories separately rebound; neckline/hand/ankle clearance and whole-rider fit are unaccepted.',
        'Boot foot region is bounded appearance extraction with leather replacement; sole/lace construction pending.',
        'This detail level is not mobile LOD qualification, exact engine proof or production player promotion. Root alone judges.']}
(evidence / 'assembly.json').write_text(json.dumps(report, indent=2) + '\n')
print('APPEARANCE_ASSEMBLED', report['GLBSHA256'], flush=True)
