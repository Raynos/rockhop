"""Headless Blender 5.2.1 Alpine kit; botanical source adapted from Pine Hollow.

Geometry is deterministic numpy; supplied CC0 map bakes are pinned inputs.
Run build.sh under the shared model lock. No .blend files are delivered.
"""
import hashlib
import json
import math
import os
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import treegen as TG
from glb import write_glb

ROOT = HERE.parents[3]
OUT = HERE / 'build'
EVIDENCE = ROOT / 'docs/evidence/course-remaster/alpine-tree-kit'
OUT.mkdir(parents=True, exist_ok=True)
EVIDENCE.mkdir(parents=True, exist_ok=True)
# Existing baked atlas cells preserve their original species slot.
ORIGINAL_SLOTS = [0, 1, 2, 3, 4, 5, 10, 11, 12, 13]
TREES = [make() for _, _, _, _, make in TG.SPECS]


def far_cross(slot, width, height):
    p, n, uv, indices = [], [], [], []
    u0, v0 = (slot % 4) / 4, (slot // 4) / 4
    for angle in (0, math.pi / 2):
        base = len(p)
        for x, y, u, v in [(-width/2, 0, u0, v0), (width/2, 0, u0+.25, v0),
                            (width/2, height, u0+.25, v0+.25), (-width/2, height, u0, v0+.25)]:
            p.append([x*math.cos(angle), y, -x*math.sin(angle)])
            n.append([math.sin(angle), 0, math.cos(angle)])
            uv.append([u, v])
        indices.extend([base, base+1, base+2, base, base+2, base+3])
    return {'POSITION': np.array(p), 'NORMAL': np.array(n), 'TEXCOORD_0': np.array(uv),
            'COLOR_0': np.ones((8, 3)), 'indices': np.array(indices)}


def combine(parts):
    g = TG.Geo()
    for part in parts:
        g.extend(part)
    a = g.arrays()
    a.pop('TEXCOORD_1', None)
    return a


def materials(phone, far=False):
    images, textures = [], []
    def tex(name):
        images.append({'uri': name + ('.phone.webp' if phone else '.png' if name.endswith('albedo') else '.jpg')})
        t = {'sampler': 0}
        if phone:
            t['extensions'] = {'EXT_texture_webp': {'source': len(images)-1}}
        else:
            t['source'] = len(images)-1
        textures.append(t)
        return {'index': len(textures)-1}
    mats = []
    if not far:
        for bark in ('pine_bark', 'fir_bark', 'bark_willow_02'):
            mats.append({'name': bark, 'pbrMetallicRoughness': {'baseColorTexture': tex(bark+'-diffuse'),
                         'metallicRoughnessTexture': tex(bark+'-arm'), 'metallicFactor': 0, 'roughnessFactor': 1},
                         'normalTexture': tex(bark+'-nor_gl')})
    mats.append({'name': 'alpine-impostor' if far else 'alpine-branches',
                 'pbrMetallicRoughness': {'baseColorTexture': tex('impostor-albedo' if far else 'cards-albedo'),
                     'metallicFactor': 0, 'roughnessFactor': .92},
                 'normalTexture': tex('impostor-normal' if far else 'cards-normal'),
                 'alphaMode': 'MASK', 'alphaCutoff': .45, 'doubleSided': True})
    if not far:
        mats[-1]['pbrMetallicRoughness']['metallicRoughnessTexture'] = tex('cards-arm')
    return mats, images, textures


meta = {'schema': 1, 'units': 'metres', 'up': '+Y', 'root': [0, 0, 0], 'variants': [],
        'lods': {'full': ['trunk', 'hi', 'twigs'], 'near': ['trunkLo', 'lo'], 'far': ['cross']},
        'candidate': True, 'runtimeAccepted': False}
for i, tr in enumerate(TREES):
    p = np.concatenate([tr.trunk.arrays()['POSITION'], tr.hi.arrays()['POSITION']])
    half = float(max(np.abs(p[:,0]).max(), np.abs(p[:,2]).max())) * 1.02
    frame_h = max(float(p[:,1].max()) * 1.02, half * 4)
    stats = tr.stats()
    meta['variants'].append({'name': tr.name, 'species': tr.species, 'height': tr.height,
                            'radius': tr.trunk_r, 'impostorSlot': ORIGINAL_SLOTS[i], 'frame': [frame_h/2, frame_h],
                            'triangles': {'full': stats['trunk']+stats['hi']+stats['twigs'],
                                          'near': stats['trunkLo']+stats['lo'], 'far': 4}, 'parts': stats})
for lod in ('full', 'near', 'far'):
    meshes = []
    for i, tr in enumerate(TREES):
        bark = 1 if tr.name.startswith('fir') or tr.name == 'sapling-fir' else 2 if tr.species == 'snag' else 0
        if lod == 'far':
            width, height = meta['variants'][i]['frame']
            meshes.append((tr.name+'__far', far_cross(ORIGINAL_SLOTS[i], width, height), 0))
        else:
            meshes.append((tr.name+'__bark', combine([tr.trunk] if lod == 'full' else [tr.trunkLo]), bark))
            meshes.append((tr.name+'__branches', combine([tr.hi, tr.twigs] if lod == 'full' else [tr.lo]), 3))
    for phone in (False, True):
        mats, images, textures = materials(phone, lod == 'far')
        write_glb(str(OUT/f'trees-{lod}{".phone" if phone else ""}.raw.glb'), meshes,
                  extras={'kit': 'alpine-trees', 'lod': lod, 'candidate': True}, materials=mats,
                  images=images, textures=textures, samplers=[{'magFilter': 9729, 'minFilter': 9987, 'wrapS': 10497, 'wrapT': 10497}])
(OUT/'trees.json').write_text(json.dumps(meta, indent=2)+'\n')
if '--geometry-only' in sys.argv:
    print('Alpine deterministic geometry complete', flush=True)
    sys.exit(0)

import bpy


def image(path, data=False):
    im = bpy.data.images.load(str(path), check_existing=True)
    if data:
        im.colorspace_settings.name = 'Non-Color'
    return im


def material(name, diffuse, normal, alpha=False):
    mat = bpy.data.materials.new(name); mat.use_nodes = True
    nt = mat.node_tree; bs = nt.nodes.get('Principled BSDF')
    td = nt.nodes.new('ShaderNodeTexImage'); td.image = image(OUT/diffuse)
    vc = nt.nodes.new('ShaderNodeVertexColor'); vc.layer_name = 'Col'
    mul = nt.nodes.new('ShaderNodeMixRGB'); mul.blend_type = 'MULTIPLY'; mul.inputs[0].default_value = 1
    nt.links.new(td.outputs['Color'], mul.inputs[1]); nt.links.new(vc.outputs['Color'], mul.inputs[2])
    nt.links.new(mul.outputs[0], bs.inputs['Base Color'])
    bs.inputs['Roughness'].default_value = .9
    tn = nt.nodes.new('ShaderNodeTexImage'); tn.image = image(OUT/normal, True)
    nm = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(tn.outputs['Color'], nm.inputs['Color'])
    nt.links.new(nm.outputs[0], bs.inputs['Normal'])
    if alpha:
        cut = nt.nodes.new('ShaderNodeMath'); cut.operation = 'GREATER_THAN'; cut.inputs[1].default_value = .45
        nt.links.new(td.outputs['Alpha'], cut.inputs[0]); nt.links.new(cut.outputs[0], bs.inputs['Alpha'])
    return mat


bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene; scene.render.engine = 'CYCLES'; scene.cycles.samples = 32
scene.cycles.use_denoising = True; scene.render.film_transparent = False
scene.view_settings.view_transform = 'AgX'
try:
    prefs = bpy.context.preferences.addons['cycles'].preferences; prefs.compute_device_type = 'METAL'; prefs.get_devices()
    for device in prefs.devices:
        device.use = True
    scene.cycles.device = 'GPU'
except Exception:
    pass
scene.world = bpy.data.worlds.new('alpine-air'); scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.42, .56, .7, 1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value = .45
bs = [material(bid, bid+'-diffuse.jpg', bid+'-nor_gl.jpg') for bid in ('pine_bark','fir_bark','bark_willow_02')]
cards = material('branches', 'cards-albedo.png', 'cards-normal.jpg', True)


def object_from(name, a, mat, x):
    p = a['POSITION']; p = np.stack([p[:,0], -p[:,2], p[:,1]], axis=1)
    triangles = a['indices'].reshape(-1,3)
    mesh = bpy.data.meshes.new(name); mesh.from_pydata(p.tolist(), [], triangles.tolist()); mesh.update()
    uv = mesh.uv_layers.new(name='UVMap'); uv.data.foreach_set('uv', a['TEXCOORD_0'][triangles.ravel()].ravel())
    color = mesh.color_attributes.new(name='Col', type='FLOAT_COLOR', domain='POINT')
    color.data.foreach_set('color', np.concatenate([a['COLOR_0'], np.ones((len(p),1))],axis=1).ravel())
    normal = a['NORMAL']; normal = np.stack([normal[:,0], -normal[:,2], normal[:,1]],axis=1)
    mesh.normals_split_custom_set_from_vertices(normal.tolist())
    mesh.materials.append(mat); ob = bpy.data.objects.new(name,mesh); scene.collection.objects.link(ob); ob.location.x = x
    return ob


x = 0
for i,tr in enumerate(TREES):
    x += max(3,tr.height*.22)
    bark = 1 if tr.name.startswith('fir') or tr.name == 'sapling-fir' else 2 if tr.species == 'snag' else 0
    object_from(tr.name+'__bark',combine([tr.trunk]),bs[bark],x)
    object_from(tr.name+'__branches',combine([tr.hi,tr.twigs]),cards,x)
    x += max(3,tr.height*.22)+2
bpy.ops.mesh.primitive_plane_add(size=600); ground=bpy.context.object
gm=bpy.data.materials.new('forest-duff'); gm.diffuse_color=(.10,.075,.035,1); ground.data.materials.append(gm)
sun_data=bpy.data.lights.new('sun','SUN'); sun_data.energy=3; sun_data.angle=.07
sun=bpy.data.objects.new('sun',sun_data); scene.collection.objects.link(sun); sun.rotation_euler=(.8,-.4,-.5)
cam_data=bpy.data.cameras.new('preview'); cam=bpy.data.objects.new('preview',cam_data); scene.collection.objects.link(cam)
from mathutils import Vector
cam.location=(x/2,-150,35); cam.rotation_euler=(Vector((x/2,0,13))-cam.location).to_track_quat('-Z','Y').to_euler()
cam_data.type='ORTHO'; cam_data.ortho_scale=x+18; cam_data.clip_end=1000
scene.camera=cam; scene.render.resolution_x=2200;scene.render.resolution_y=800;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.filepath=str(EVIDENCE/'lineup.png');bpy.ops.render.render(write_still=True)
print('Alpine kit source build complete', flush=True)
