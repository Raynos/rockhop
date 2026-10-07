"""Construct selected donor face and a welded anatomical neck on the shared rig.

The approved carrier's raw positions already cancel its historical skin bind.
The only additional transform is a proper frame change and uniform height fit.
"""
import hashlib
import json
import struct
from pathlib import Path

DONOR = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/body-bind11/rider.glb')
DONOR_SHA = 'b7f4f22790124c664f9907104e5b17b77775b4c5c995f715d62be640bbcc8754'
SOURCE_CUT_Y = 1.56
BODY_CUT_Z = 1.505


def buildFace(body, rig, out):
    import bpy
    import bmesh
    import numpy as np
    from mathutils import Vector

    out = Path(out) / 'selected-face01'
    out.mkdir(parents=True, exist_ok=False)
    raw = DONOR.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == DONOR_SHA
    size, _ = struct.unpack_from('<II', raw, 12)
    doc = json.loads(raw[20:20 + size])
    binary = memoryview(raw)[28 + size:]

    def accessor(index):
        a = doc['accessors'][index]; view = doc['bufferViews'][a['bufferView']]
        dtype = {5126: '<f4', 5125: '<u4', 5123: '<u2', 5121: 'u1'}[a['componentType']]
        columns = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']]
        width = np.dtype(dtype).itemsize
        return np.ndarray((a['count'], columns), dtype=dtype, buffer=binary,
                          offset=view.get('byteOffset', 0) + a.get('byteOffset', 0),
                          strides=(view.get('byteStride', width * columns), width)).copy()

    head_node = next(n for n in doc['nodes'] if n.get('name') == 'textured')
    primitives = doc['meshes'][head_node['mesh']]['primitives']
    assert [doc['accessors'][p['attributes']['POSITION']]['count'] for p in primitives] == [61099, 294]
    scale = 1.78 / 1.8225715160369873
    top = SOURCE_CUT_Y * scale
    assert top > BODY_CUT_Z
    # Import obtains the genuine PBR graphs and packed image data. Geometry below
    # is constructed from raw arrays, bypassing the historical root transform.
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(DONOR), merge_vertices=False)
    imported = set(bpy.data.objects) - before
    source_object = next(o for o in imported if o.type == 'MESH' and len(o.data.vertices) == 61393)
    source_materials = list(source_object.data.materials)
    assert len(source_materials) == 2
    for obj in imported:
        bpy.data.objects.remove(obj, do_unlink=True)
    material_indices = []
    for mat in source_materials:
        material_indices.append(len(body.data.materials)); body.data.materials.append(mat)
    groups = {g.name: g.index for g in body.vertex_groups}
    assert all(n in groups for n in ('DEF-spine.004', 'DEF-spine.005', 'DEF-spine.006'))
    bm = bmesh.new(); bm.from_mesh(body.data)
    deform = bm.verts.layers.deform.verify()
    source_vertex = bm.verts.layers.int.get('_SOURCE_VERTEX_ID') or bm.verts.layers.int.new('_SOURCE_VERTEX_ID')
    uv = bm.loops.layers.uv.verify()
    normals = bm.loops.layers.float_vector.new('RetainedSourceNormal')
    source_face = bm.faces.layers.int.new('SelectedSourceFace')
    for face in bm.faces:
        face[source_face] = -1
        for loop in face.loops:
            loop[normals] = loop.vert.normal
    bmesh.ops.bisect_plane(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces),
                          plane_co=(0, 0, BODY_CUT_Z), plane_no=(0, 0, 1),
                          clear_outer=True, clear_inner=False, dist=1e-7)
    bm.normal_update()

    def loops_at(z):
        edges = [e for e in bm.edges if e.is_boundary and
                 all(abs(v.co.z - z) < 3e-6 for v in e.verts)]
        adjacency = {}
        for edge in edges:
            for vertex in edge.verts:
                adjacency.setdefault(vertex, []).append(edge)
        assert all(len(rows) == 2 for rows in adjacency.values()), 'Neck cut must have closed degree-two loops'
        remaining = set(edges); result = []
        while remaining:
            first = next(iter(remaining)); start = first.verts[0]; current = start
            ring = []
            while True:
                ring.append(current)
                edge = next(e for e in adjacency[current] if e in remaining)
                remaining.remove(edge); current = edge.other_vert(current)
                if current == start: break
            result.append(ring)
        return result

    body_rings = loops_at(BODY_CUT_Z)
    assert len(body_rings) == 1
    lower = body_rings[0]
    retained = []
    raw_lookup = {}
    source_faces_added = []
    for part, primitive in enumerate(primitives):
        points = accessor(primitive['attributes']['POSITION'])
        source_normals = accessor(primitive['attributes']['NORMAL'])
        source_uv = accessor(primitive['attributes']['TEXCOORD_0'])
        faces = accessor(primitive['indices']).reshape(-1, 3)
        mapping = []
        for index, row in enumerate(points):
            key = tuple(float(x) for x in row)
            if key not in raw_lookup:
                vertex = bm.verts.new((-row[2] * scale, -(row[0] - .65) * scale, row[1] * scale))
                vertex[source_vertex] = 1000000 + part * 100000 + index
                raw_lookup[key] = vertex
            mapping.append(raw_lookup[key])
        for index, triangle in enumerate(faces):
            vertices = [mapping[int(i)] for i in triangle]
            if len(set(vertices)) < 3: continue
            try: face = bm.faces.new(vertices)
            except ValueError: continue
            face.material_index = material_indices[part]; face.smooth = True
            face[source_face] = part * 1000000 + index
            for loop, original in zip(face.loops, triangle):
                original = int(original); row = source_normals[original]
                loop[normals] = Vector((-row[2], -row[0], row[1])).normalized()
                loop[uv].uv = (float(source_uv[original][0]), 1 - float(source_uv[original][1]))
            source_faces_added.append(face)
            if all(points[int(i)][1] > SOURCE_CUT_Y + 1e-5 for i in triangle):
                retained.append((face[source_face], [list(v.co) for v in vertices],
                                 [list(loop[uv].uv) for loop in face.loops],
                                 [list(loop[normals]) for loop in face.loops]))
    head_vertices = set(raw_lookup.values())
    head_edges = {e for f in source_faces_added for e in f.edges}
    bmesh.ops.bisect_plane(bm, geom=list(head_vertices) + list(head_edges) + source_faces_added,
                          plane_co=(0, 0, top), plane_no=(0, 0, 1),
                          clear_inner=True, clear_outer=False, dist=1e-7)
    bm.normal_update()
    head_rings = loops_at(top)
    assert len(head_rings) == 2, ('Actual selected neck has two nested openings', len(head_rings))

    def area(ring):
        return sum(a.co.x * b.co.y - b.co.x * a.co.y for a, b in zip(ring, ring[1:] + ring[:1])) / 2

    outer, inner = sorted(head_rings, key=lambda ring: abs(area(ring)), reverse=True)
    # These rings are genuine anatomical section vertices. CCW ordering gives
    # outward bridge faces and the opposite directed edge to the donor surface.
    def ccw(ring):
        if area(ring) < 0: ring = list(reversed(ring))
        start = min(range(len(ring)), key=lambda i: (ring[i].co.y, abs(ring[i].co.x)))
        return ring[start:] + ring[:start]
    lower = ccw(lower); outer = ccw(outer)

    def normalized(field):
        four = sorted(((k, v) for k, v in field.items() if v > 0), key=lambda item: (-item[1], item[0]))[:4]
        total = sum(v for _, v in four)
        assert total > 0
        return {k: v / total for k, v in four}

    def set_field(vertex, field):
        vertex[deform].clear()
        for key, value in field.items(): vertex[deform][key] = value

    for vertex in lower:
        field = normalized(dict(vertex[deform]))
        set_field(vertex, field)

    def head_field(z):
        t = max(0, min(1, (z - top) / .070)); t = t * t * (3 - 2 * t)
        return {groups['DEF-spine.005']: .65 * (1 - t), groups['DEF-spine.006']: .35 + .65 * t}

    for vertex in head_vertices:
        if vertex.is_valid:
            set_field(vertex, normalized(head_field(vertex.co.z)))
    for vertex in outer + inner:
        set_field(vertex, normalized(head_field(top)))

    def arc(ring):
        distances = [0.]
        for a, b in zip(ring, ring[1:] + ring[:1]): distances.append(distances[-1] + (a.co - b.co).length)
        return [d / distances[-1] for d in distances]

    low_arc, high_arc = arc(lower), arc(outer)
    def sample(ring, fractions, t):
        i = next((i for i in range(len(ring)) if fractions[i + 1] >= t), len(ring) - 1)
        factor = (t - fractions[i]) / (fractions[i + 1] - fractions[i])
        a, b = ring[i], ring[(i + 1) % len(ring)]
        field = {}
        for vertex, weight in ((a, 1 - factor), (b, factor)):
            for key, value in vertex[deform].items(): field[key] = field.get(key, 0) + value * weight
        return a.co.lerp(b.co, factor), a.normal.lerp(b.normal, factor).normalized(), normalized(field)

    def tangent(normal):
        direction = Vector((0, 0, 1)) - normal * normal.z
        assert direction.z > .03, 'Anatomical neck tangent must ascend'
        return direction / direction.z * (top - BODY_CUT_Z)

    outer_uv = [next(loop[uv].uv.copy() for loop in v.link_loops if loop.face[source_face] >= 0) for v in outer]
    rings = [lower]
    max_tangent = 0.
    for t in (.25, .5, .75):
        ring = []
        for i, upper in enumerate(outer):
            position, normal, field = sample(lower, low_arc, high_arc[i])
            lo_tangent, hi_tangent = tangent(normal), tangent(upper.normal)
            max_tangent = max(max_tangent, lo_tangent.length, hi_tangent.length)
            co = ((2*t**3 - 3*t*t + 1)*position + (t**3 - 2*t*t + t)*lo_tangent
                  + (-2*t**3 + 3*t*t)*upper.co + (t**3 - t*t)*hi_tangent)
            vertex = bm.verts.new(co)
            vertex[source_vertex] = -1
            blend = t*t*(3-2*t); upper_field = head_field(top)
            combined = {k: v * (1-blend) for k, v in field.items()}
            for key, value in upper_field.items(): combined[key] = combined.get(key, 0) + blend*value
            set_field(vertex, normalized(combined)); ring.append(vertex)
        rings.append(ring)
    rings.append(outer)
    bridge_faces = []
    for low, high in zip(rings, rings[1:]):
        a_arc, b_arc = arc(low), arc(high); i = j = 0
        while i < len(low) or j < len(high):
            if j == len(high) or (i < len(low) and a_arc[i+1] <= b_arc[j+1]):
                vertices = [low[i % len(low)], low[(i+1) % len(low)], high[j % len(high)]]; i += 1
            else:
                vertices = [low[i % len(low)], high[(j+1) % len(high)], high[j % len(high)]]; j += 1
            face = bm.faces.new(vertices); face.material_index = material_indices[0]; face.smooth = True; face[source_face] = -2
            for loop in face.loops:
                nearest = min(range(len(outer)), key=lambda k: (outer[k].co.xy - loop.vert.co.xy).length_squared)
                loop[uv].uv = outer_uv[nearest]
            bridge_faces.append(face)
    # Close only the internal cavity's actual cut, in opposite edge orientation.
    edge = next(e for e in inner[0].link_edges if e.is_boundary and inner[1] in e.verts)
    adjacent = edge.link_loops[0]
    if adjacent.vert == inner[0]: inner = list(reversed(inner))
    cap = bm.faces.new(inner); cap.material_index = material_indices[0]; cap[source_face] = -3
    for loop in cap.loops: loop[uv].uv = outer_uv[0]
    bmesh.ops.triangulate(bm, faces=[cap])
    bm.normal_update()
    winding_errors = sum(e.link_loops[0].vert == e.link_loops[1].vert
                         for e in bm.edges if len(e.link_loops) == 2)
    assert winding_errors == 0, ('Joined surface edges must have opposite directed corners', winding_errors)
    # Only neck/new bridge normals are geometric. Protected source corners keep
    # their original shading normals and UV charts exactly.
    for face in bm.faces:
        if face[source_face] < 0:
            for loop in face.loops: loop[normals] = loop.vert.normal
    snapshots = {f[source_face]: f for f in bm.faces if f[source_face] >= 0}
    position_error = uv_error = normal_error = 0.
    for identity, positions, uvs, original_normals in retained:
        face = snapshots[identity]
        assert len(face.verts) == 3
        for loop, position, original_uv, original_normal in zip(face.loops, positions, uvs, original_normals):
            position_error = max(position_error, (loop.vert.co - Vector(position)).length)
            uv_error = max(uv_error, (loop[uv].uv - Vector(original_uv)).length)
            normal_error = max(normal_error, (Vector(loop[normals]) - Vector(original_normal)).length)
    assert position_error == uv_error == normal_error == 0
    # Compute an exposed skin value directly from the genuine source albedo.
    principal = source_materials[0].node_tree.nodes.get('Principled BSDF')
    image_node = principal.inputs['Base Color'].links[0].from_node
    image = image_node.image
    width, height = image.size
    samples = []
    for value in outer_uv:
        x = min(width-1, max(0, int(value.x * width)))
        y = min(height-1, max(0, int(value.y * height)))
        offset = 4 * (y * width + x)
        samples.append(image.pixels[offset:offset+3])
    assert image.colorspace_settings.name == 'sRGB'
    skin_encoded = np.median(np.asarray(samples), axis=0)
    # Independent raw PNG readback proves Blender's sampled values here match
    # encoded 8-bit channels. Constant Principled colors use linear RGB.
    skin_linear = np.where(skin_encoded <= .04045, skin_encoded / 12.92,
                           ((skin_encoded + .055) / 1.055) ** 2.4)
    body_mat = body.data.materials[0]; body_mat.diffuse_color = (*map(float, skin_linear), 1)
    body_mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value = (*map(float, skin_linear), 1)
    boundaries = sum(e.is_boundary for e in bm.edges)
    nonmanifold = sum(not e.is_manifold for e in bm.edges)
    assert boundaries == 0 and nonmanifold == 0, ('Head/body join must be closed manifold', boundaries, nonmanifold)
    seen = set(); components = 0
    for vertex in bm.verts:
        if vertex in seen: continue
        components += 1; stack = [vertex]; seen.add(vertex)
        while stack:
            for edge in stack.pop().link_edges:
                for v in edge.verts:
                    if v not in seen: seen.add(v); stack.append(v)
    assert components == 1, ('Actual face, bridge and wearer must form one component', components)
    bm.verts.index_update(); bm.faces.index_update()
    corner_normals = [tuple(loop[normals]) for face in bm.faces for loop in face.loops]
    report = {'accepted': False, 'source': str(DONOR), 'sourceSHA256': DONOR_SHA,
              'properFrame': '[-rawZ,-(rawX-.65),rawY]', 'uniformScale': scale,
              'historicalRootAppliedAgain': False, 'sourceCutY': SOURCE_CUT_Y,
              'bodyCutNativeZ': BODY_CUT_Z, 'donorCutNativeZ': top,
              'lowerBoundaryVertices': len(lower), 'donorOuterBoundaryVertices': len(outer),
              'donorInnerBoundaryVertices': len(inner), 'bridgeTriangles': len(bridge_faces),
              'protectedSourceTriangles': len(retained), 'protectedPositionMaximumErrorM': position_error,
              'protectedUVMaximumError': uv_error, 'closedSurfaceComponents': components,
              'protectedCornerNormalMaximumError': normal_error,
              'boundaryEdges': boundaries, 'nonmanifoldEdges': nonmanifold,
              'oppositeEdgeWindingErrors': winding_errors,
              'bridgeMaximumEndpointTangentM': max_tangent, 'neckAlbedoImage': image.name,
              'sourceSampledSkinLinearRGB': list(map(float, skin_linear)),
              'sourceSampledSkinEncodedSRGB': list(map(float, skin_encoded)),
              'limits': ['Native construction only; actual moving profile and normal/tangent continuity require parent review.']}
    bm.to_mesh(body.data); bm.free(); body.data.update()
    assert len(corner_normals) == len(body.data.loops)
    body.data.normals_split_custom_set(corner_normals)
    for vertex in body.data.vertices:
        assert len([g for g in vertex.groups if g.weight > 0]) <= 4
    for obj in list(bpy.context.scene.objects):
        if obj.type == 'MESH' and ('.eye.' in obj.name or obj.name in ('RiderBrows', 'RiderBuzzcut')):
            bpy.data.objects.remove(obj, do_unlink=True)
    report['vertices'] = len(body.data.vertices); report['triangles'] = sum(len(p.vertices)-2 for p in body.data.polygons)
    report_path = out / 'report.json'; report_path.write_text(json.dumps(report, indent=2) + '\n')
    return {'objects': [], 'materials': source_materials, 'report': report, 'reportPath': str(report_path)}
