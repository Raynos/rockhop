"""Exact retained donor witnesses; no evaluation of unrelated master meshes."""
import hashlib
import json
import struct

import bpy
import numpy as np


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def array_sha(collection, attribute, width, dtype):
    data = np.empty(len(collection) * width, dtype)
    collection.foreach_get(attribute, data)
    return hashlib.sha256(data.tobytes()).hexdigest()


def matrix(value):
    return [list(row) for row in value]


def scalar_properties(item):
    result = {}
    for prop in item.bl_rna.properties:
        if prop.is_readonly or prop.type not in {'BOOLEAN', 'INT', 'FLOAT', 'STRING', 'ENUM'}:
            continue
        value = getattr(item, prop.identifier)
        if getattr(prop, 'is_array', False):
            value = list(value)
        if isinstance(value, set):
            value = sorted(value)
        result[prop.identifier] = value
    return result


def materials(objects):
    result = {}; images = {}; trees = {}

    def tree(node_tree):
        if node_tree.name_full in trees:
            return
        trees[node_tree.name_full] = None
        nodes = []
        for node in node_tree.nodes:
            row = {'name': node.name, 'type': node.bl_idname, 'properties': scalar_properties(node), 'inputs': []}
            for socket in node.inputs:
                if hasattr(socket, 'default_value'):
                    value = socket.default_value
                    if isinstance(value, bpy.types.ID):
                        value = [value.bl_rna.identifier, value.name_full]
                    elif value is not None and not isinstance(value, (bool, str, float, int)):
                        value = list(value)
                    row['inputs'].append([socket.identifier, value])
            if getattr(node, 'node_tree', None):
                row['nodeTree'] = node.node_tree.name_full
                tree(node.node_tree)
            if getattr(node, 'image', None):
                im = node.image
                assert im.packed_file, ('Selected source image must remain packed', im.name)
                row['image'] = im.name_full
                if im.name_full not in images:
                    images[im.name_full] = {'packedSHA256': hashlib.sha256(im.packed_file.data).hexdigest(),
                        'dimensions': list(im.size), 'source': im.source, 'colorSpace': im.colorspace_settings.name,
                        'alphaMode': im.alpha_mode, 'isFloat': im.is_float}
            nodes.append(row)
        trees[node_tree.name_full] = {'nodes': nodes, 'links': sorted([
            (l.from_node.name, l.from_socket.identifier, l.to_node.name, l.to_socket.identifier)
            for l in node_tree.links])}

    for obj in objects:
        for material in obj.data.materials:
            assert material and material.use_nodes
            result[material.name_full] = {'properties': scalar_properties(material), 'tree': material.node_tree.name_full}
            tree(material.node_tree)
    return {'graphSHA256': digest({'materials': result, 'trees': trees}), 'images': images}


def source(obj):
    mesh = obj.data
    weights = hashlib.sha256()
    for vertex in mesh.vertices:
        weights.update(struct.pack('<II', vertex.index, len(vertex.groups)))
        for item in vertex.groups:
            weights.update(struct.pack('<If', item.group, item.weight))
    keys = {}
    if mesh.shape_keys:
        for key in mesh.shape_keys.key_blocks:
            keys[key.name] = array_sha(key.data, 'co', 3, np.float32)
    return {'mesh': mesh.name_full, 'vertices': len(mesh.vertices), 'polygons': len(mesh.polygons),
        'positionSHA256': array_sha(mesh.vertices, 'co', 3, np.float32),
        'edgeSHA256': array_sha(mesh.edges, 'vertices', 2, np.int32),
        'loopVertexSHA256': array_sha(mesh.loops, 'vertex_index', 1, np.int32),
        'polygonStartSHA256': array_sha(mesh.polygons, 'loop_start', 1, np.int32),
        'polygonSizeSHA256': array_sha(mesh.polygons, 'loop_total', 1, np.int32),
        'materialIndexSHA256': array_sha(mesh.polygons, 'material_index', 1, np.int32),
        'uv': {layer.name: {'sha256': array_sha(layer.data, 'uv', 2, np.float32),
                           'activeRender': layer.active_render} for layer in mesh.uv_layers},
        'activeUV': mesh.uv_layers.active.name if mesh.uv_layers.active else None,
        'groups': [(g.index, g.name, g.lock_weight) for g in obj.vertex_groups], 'weightSHA256': weights.hexdigest(),
        'shapeKeys': keys, 'materials': [m.name_full if m else None for m in mesh.materials],
        'modifiers': [{'name': mod.name, 'type': mod.type, 'properties': scalar_properties(mod),
                       'objectReferences': {prop.identifier: label.name_full if label else None
                           for prop in mod.bl_rna.properties if prop.type == 'POINTER'
                           and isinstance((label := getattr(mod, prop.identifier)), (bpy.types.ID, type(None)))}}
                      for mod in obj.modifiers],
        'parent': obj.parent.name_full if obj.parent else None, 'matrixWorld': matrix(obj.matrix_world),
        'matrixParentInverse': matrix(obj.matrix_parent_inverse)}


def rig(obj):
    return {'object': obj.name_full, 'matrixWorld': matrix(obj.matrix_world), 'bones': [
        {'name': bone.name, 'parent': bone.parent.name if bone.parent else None,
         'matrixLocal': matrix(bone.matrix_local), 'head': list(bone.head_local),
         'tail': list(bone.tail_local), 'useDeform': bone.use_deform}
        for bone in obj.data.bones]}


def retained(sources, armature):
    return {'sources': {name: source(obj) for name, obj in sources.items()},
            'materials': materials(sources.values()), 'rig': rig(armature)}
