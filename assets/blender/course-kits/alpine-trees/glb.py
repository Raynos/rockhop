"""glb.py — a minimal glTF 2.0 binary writer for the tree set (numpy arrays in, one node + mesh per part)."""
import json
import struct
import numpy as np

FLOAT, UINT, USHORT = 5126, 5125, 5123
ARRAY, ELEMENT = 34962, 34963
TYPES = {1: 'SCALAR', 2: 'VEC2', 3: 'VEC3', 4: 'VEC4'}


def write_glb(path, meshes, extras=None, materials=None, images=None, textures=None, samplers=None):
    """meshes: [(name, {'POSITION': (n,3) f32, 'NORMAL', 'TEXCOORD_0', 'TEXCOORD_1', 'COLOR_0', 'indices': (m,) u32})]"""
    blob = bytearray()
    views, accessors, gmeshes, nodes = [], [], [], []

    def push(arr, target, comp, minmax=False):
        while len(blob) % 4:
            blob.append(0)
        off = len(blob)
        blob.extend(arr.tobytes())
        views.append({'buffer': 0, 'byteOffset': off, 'byteLength': int(arr.nbytes), 'target': target})
        width = 1 if arr.ndim == 1 else arr.shape[1]
        acc = {'bufferView': len(views) - 1, 'componentType': comp, 'count': int(arr.shape[0]), 'type': TYPES[width]}
        if minmax:
            acc['min'] = [float(x) for x in arr.min(axis=0)]
            acc['max'] = [float(x) for x in arr.max(axis=0)]
        accessors.append(acc)
        return len(accessors) - 1

    for item in meshes:
        name, a = item[:2]
        material = item[2] if len(item) > 2 else None
        attrs = {}
        for key in ('POSITION', 'NORMAL', 'TEXCOORD_0', 'TEXCOORD_1', 'COLOR_0'):
            if key in a:
                values = np.ascontiguousarray(a[key], dtype=np.float32)
                if key == 'TEXCOORD_0':
                    # Botanical source/Blender uses bottom-origin UVs. glTF images
                    # load with flipY=false, so preserve atlas cells by inverting V.
                    values = values.copy()
                    values[:, 1] = 1.0 - values[:, 1]
                attrs[key] = push(values, ARRAY, FLOAT, minmax=key == 'POSITION')
        idx = a['indices']
        if int(idx.max()) < 65535:
            ind = push(np.ascontiguousarray(idx, dtype=np.uint16), ELEMENT, USHORT)
        else:
            ind = push(np.ascontiguousarray(idx, dtype=np.uint32), ELEMENT, UINT)
        primitive = {'attributes': attrs, 'indices': ind, 'mode': 4}
        if material is not None:
            primitive['material'] = material
        gmeshes.append({'name': name, 'primitives': [primitive]})
        nodes.append({'name': name, 'mesh': len(gmeshes) - 1})

    while len(blob) % 4:
        blob.append(0)
    doc = {
        'asset': {'version': '2.0', 'generator': 'Rockhop Alpine kit, adapted Wildshard Pine Hollow'},
        'scene': 0, 'scenes': [{'nodes': list(range(len(nodes)))}],
        'nodes': nodes, 'meshes': gmeshes, 'accessors': accessors, 'bufferViews': views,
        'buffers': [{'byteLength': len(blob)}],
    }
    for key, value in [('materials', materials), ('images', images), ('textures', textures), ('samplers', samplers)]:
        if value:
            doc[key] = value
    if textures and any('extensions' in texture for texture in textures):
        doc['extensionsUsed'] = ['EXT_texture_webp']
        doc['extensionsRequired'] = ['EXT_texture_webp']
    if extras:
        doc['extras'] = extras
    js = json.dumps(doc, separators=(',', ':')).encode()
    while len(js) % 4:
        js += b' '
    total = 12 + 8 + len(js) + 8 + len(blob)
    with open(path, 'wb') as f:
        f.write(struct.pack('<III', 0x46546C67, 2, total))
        f.write(struct.pack('<II', len(js), 0x4E4F534A)); f.write(js)
        f.write(struct.pack('<II', len(blob), 0x004E4942)); f.write(bytes(blob))
