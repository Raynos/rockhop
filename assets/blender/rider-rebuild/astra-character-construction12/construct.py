"""Selected rider wrist surgery. Run only under the parent's bounded CPU2 lease.

Source vertices/corners are recorded explicitly. New interior surfaces are
selected-material lining, not a replacement exterior or a rendered body mask.
"""
import hashlib
import json
import runpy
import sys
from collections import defaultdict, deque
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import tessellate_polygon, delaunay_2d_cdt

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
V, A = {}, {}
VISIBLE = {'RiderBody', 'RiderHoodie', 'RiderJeans', 'ActualSelectedGlove.L',
           'ActualSelectedGlove.R', 'ActualSelectedBoot.L', 'ActualSelectedBoot.R'}
EDITED = ('RiderHoodie', 'ActualSelectedGlove.L', 'ActualSelectedGlove.R')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while block := stream.read(1048576):
            h.update(block)
    return h.hexdigest()


def pin(row):
    path = ROOT/row['path']
    assert sha(path) == row['sha256'], ('Changed input', row['path'])
    return path


def smooth(x):
    return V['smooth'](x)


def unit(v):
    return v/np.linalg.norm(v)


def tree(points, faces):
    return BVHTree.FromPolygons([Vector(p) for p in points], faces.tolist(), all_triangles=True)


def hit_radius(bvh, origin, direction):
    hit = bvh.ray_cast(Vector(origin), Vector(direction), 0.3)
    return None if hit[0] is None else float(hit[3])


class Surgery:
    """Triangle surgery with original vertices retained as an explicit prefix."""
    def __init__(self, obj, source):
        self.obj = obj
        self.base_local, self.base_world = A['points'](obj)
        mesh = obj.data
        assert all(len(p.vertices) == 3 for p in mesh.polygons), 'FACE attribute ancestry requires the selected native triangle mesh'
        mesh.calc_loop_triangles()
        self.base_faces = A['faces'](obj)
        corners = np.empty(self.base_faces.shape, dtype=np.int32)
        mesh.loop_triangles.foreach_get('loops', corners.ravel())
        self.base_corners = corners
        uv = np.empty((len(mesh.loops), 2), dtype=np.float32)
        mesh.uv_layers.active.data.foreach_get('uv', uv.ravel())
        self.base_uv = uv
        assert len(mesh.uv_layers) == 1, 'Unexpected selected UV layout'
        self.uv_flags = (mesh.uv_layers.active.active_render, mesh.uv_layers.active.active_clone)
        self.base_normals = np.empty((len(mesh.corner_normals), 3), dtype=np.float32)
        mesh.corner_normals.foreach_get('vector', self.base_normals.ravel())
        self.base_material = np.array([t.material_index for t in mesh.loop_triangles], dtype=np.int16)
        self.base_smooth = np.array([mesh.polygons[t.polygon_index].use_smooth for t in mesh.loop_triangles])
        assert source.shape == self.base_world.shape
        self.source = [p.copy() for p in source]
        self.world = [p.copy() for p in self.base_world]
        self.parents = [[i, -1, -1] for i in range(len(source))]
        self.coefficients = [[1., 0., 0.] for _ in source]
        self.vertex_roles = [0 for _ in source]
        self.faces = self.base_faces.tolist()
        self.face_sources = list(range(len(self.faces)))
        self.face_roles = [0 for _ in self.faces]
        self.corner_sources = corners.tolist()
        self.uv = [p.copy() for p in uv[corners]]
        self.material = self.base_material.tolist()
        self.smooth = self.base_smooth.tolist()
        self.affected_faces = set()
        self.affected_vertices = set()
        self.old_count = len(source)
        self.old_face_count = len(self.faces)
        self.edge_cache = {}
        self.group_names = [group.name for group in obj.vertex_groups]
        assert [group.index for group in obj.vertex_groups] == list(range(len(self.group_names)))
        self.old_weights = []
        for vertex in mesh.vertices:
            self.old_weights.append({g.group: g.weight for g in vertex.groups})

    def add(self, source, world, parents, coeffs, role):
        i = len(self.world)
        self.source.append(np.asarray(source).copy())
        self.world.append(np.asarray(world).copy())
        self.parents.append(list(parents))
        self.coefficients.append(list(coeffs))
        self.vertex_roles.append(role)
        self.affected_vertices.update(p for p in parents if p >= 0)
        return i

    def interpolate_vertex(self, a, b, t):
        key = tuple(sorted((a, b)))
        if key in self.edge_cache:
            return self.edge_cache[key]
        assert a < self.old_count and b < self.old_count
        index = self.add((1-t)*self.source[a]+t*self.source[b],
                         (1-t)*self.world[a]+t*self.world[b],
                         [a, b, -1], [1-t, t, 0.], 2)
        self.edge_cache[key] = index
        return index

    def cut(self, signed, candidates, keep_both=False):
        """Clip original triangles and interpolate their actual corner UVs."""
        nf, ns, nr, nc, nu, nm, smooths = [], [], [], [], [], [], []
        for index, face in enumerate(self.faces):
            d = signed[face]
            if not candidates[index] or np.max(d) < -1e-10:
                packets = [(face, self.uv[index], self.corner_sources[index], self.face_roles[index])]
            elif np.min(d) > 1e-10:
                packets = [(face, self.uv[index], self.corner_sources[index], self.face_roles[index])] if keep_both else []
                if not keep_both:
                    self.affected_faces.add(self.face_sources[index])
                    self.affected_vertices.update(face)
            else:
                self.affected_faces.add(self.face_sources[index])
                self.affected_vertices.update(face)
                packets = []
                for sign in ((-1, 1) if keep_both else (-1,)):
                    polygon = []
                    for k in range(3):
                        j = (k+1) % 3
                        a, b = face[k], face[j]
                        inside = sign*d[k] >= -1e-10
                        if inside:
                            polygon.append((a, self.uv[index][k], self.corner_sources[index][k]))
                        if d[k]*d[j] < -1e-20:
                            t = float(d[k]/(d[k]-d[j]))
                            n = self.interpolate_vertex(a, b, t)
                            polygon.append((n, (1-t)*self.uv[index][k].astype(float)+t*self.uv[index][j].astype(float), -1))
                    for k in range(1, len(polygon)-1):
                        tri = [polygon[0], polygon[k], polygon[k+1]]
                        if len({p[0] for p in tri}) == 3:
                            packets.append(([p[0] for p in tri], np.array([p[1] for p in tri]),
                                            [p[2] for p in tri], 1))
            for face_out, uv_out, corner_out, role in packets:
                nf.append(face_out); ns.append(self.face_sources[index]); nr.append(role)
                nc.append(corner_out); nu.append(uv_out); nm.append(self.material[index]); smooths.append(self.smooth[index])
        self.faces, self.face_sources, self.face_roles = nf, ns, nr
        self.corner_sources, self.uv, self.material, self.smooth = nc, nu, nm, smooths

    def delete(self, ids):
        ids = set(ids)
        for i in ids:
            self.affected_faces.add(self.face_sources[i])
            self.affected_vertices.update(v for v in self.faces[i] if v < self.old_count)
        keep = [i for i in range(len(self.faces)) if i not in ids]
        for key in ('faces', 'face_sources', 'face_roles', 'corner_sources', 'uv', 'material', 'smooth'):
            values = getattr(self, key)
            setattr(self, key, [values[i] for i in keep])

    def add_face(self, face, uv, material=0):
        self.faces.append(list(face)); self.uv.append(np.asarray(uv)); self.face_sources.append(-1)
        self.face_roles.append(2); self.corner_sources.append([-1]*3)
        self.material.append(material); self.smooth.append(True)

    def move(self, result, changed):
        assert len(result) == len(self.world)
        self.world = [p.copy() for p in result]
        for i in changed:
            if i < self.old_count:
                self.vertex_roles[i] = 1
                self.affected_vertices.add(int(i))

    def remove_degenerates(self):
        xyz, f = np.asarray(self.world), np.asarray(self.faces)
        area = np.linalg.norm(np.cross(xyz[f[:, 1]]-xyz[f[:, 0]], xyz[f[:, 2]]-xyz[f[:, 0]]), axis=1)
        bad = np.flatnonzero(area < 1e-13)
        authorized = [i for i in bad if self.face_sources[i] in self.affected_faces or any(v in self.affected_vertices for v in f[i])]
        inherited = [int(self.face_sources[i]) for i in bad if i not in set(authorized)]
        self.delete(authorized)
        return {'removedLocalFaces': len(authorized), 'unchangedInheritedFaces': inherited,
                'limits': 'Unchanged inherited degenerates remain reported failures; only local authorized degenerates are removed.'}

    def weights(self, vertex):
        accum = defaultdict(float)
        for parent, factor in zip(self.parents[vertex], self.coefficients[vertex]):
            if parent >= 0 and factor:
                for group, weight in self.old_weights[parent].items():
                    accum[group] += factor*weight
        keep = sorted(accum.items(), key=lambda p: (-p[1], self.group_names[p[0]]))[:4]
        total = sum(w for _, w in keep)
        assert total > 0
        return {g: w/total for g, w in keep}

    def copy_attributes(self, old, new, corner_source, untouched_corners):
        formats = {'FLOAT': ('value', 1, np.float32), 'INT': ('value', 1, np.int32),
                   'BOOLEAN': ('value', 1, np.bool_), 'FLOAT_VECTOR': ('vector', 3, np.float32),
                   'FLOAT2': ('vector', 2, np.float32), 'FLOAT_COLOR': ('color', 4, np.float32),
                   'BYTE_COLOR': ('color', 4, np.float32), 'INT8': ('value', 1, np.int32),
                   'INT32_2D': ('value', 2, np.int32), 'INT16_2D': ('value', 2, np.int16)}
        structural = {'position', '.edge_verts', '.corner_vert', '.corner_edge'}
        source_edges = {tuple(sorted(edge.vertices)): edge.index for edge in old.edges}
        for attr in old.attributes:
            if attr.name in structural or attr.name in {layer.name for layer in old.uv_layers}:
                continue
            assert attr.data_type in formats, ('Unsupported preserved attribute', attr.name, attr.data_type)
            prop, width, dtype = formats[attr.data_type]
            before = np.empty((len(attr.data), width), dtype=dtype)
            attr.data.foreach_get(prop, before.ravel())
            destination = new.attributes.get(attr.name)
            if destination is None:
                destination = new.attributes.new(attr.name, attr.data_type, attr.domain)
            values = np.empty((len(destination.data), width), dtype=dtype)
            destination.data.foreach_get(prop, values.ravel())
            if attr.domain == 'POINT':
                values[:self.old_count] = before
                for index in range(self.old_count, len(values)):
                    parents = np.asarray(self.parents[index]); coeffs = np.asarray(self.coefficients[index])
                    valid = parents >= 0
                    if np.issubdtype(dtype, np.floating):
                        values[index] = np.sum(before[parents[valid]]*coeffs[valid, None], axis=0)
                    else:
                        values[index] = before[parents[np.argmax(coeffs)]]
            elif attr.domain == 'CORNER':
                take = corner_source >= 0
                if 'normal' in attr.name.lower():
                    take &= untouched_corners
                values[take] = before[corner_source[take]]
            elif attr.domain == 'FACE':
                ids = np.asarray(self.face_sources)
                take = ids >= 0
                values[take] = before[ids[take]]
            elif attr.domain == 'EDGE':
                for edge in new.edges:
                    identity = source_edges.get(tuple(sorted(edge.vertices)))
                    if identity is not None:
                        values[edge.index] = before[identity]
            else:
                raise AssertionError(('Unsupported preserved attribute domain', attr.name, attr.domain))
            destination.data.foreach_set(prop, values.ravel())
        new.update()

    def finish(self, out):
        world = np.asarray(self.world)
        local = V['apply'](world, np.linalg.inv(np.asarray(self.obj.matrix_world))).astype(np.float32)
        untouched_vertices = np.asarray(self.vertex_roles) == 0
        local[untouched_vertices] = self.base_local[np.flatnonzero(untouched_vertices)]
        old = self.obj.data
        mesh = bpy.data.meshes.new(self.obj.name+'__Constructed12')
        mesh.from_pydata(local.tolist(), [], self.faces)
        for material in old.materials:
            mesh.materials.append(material)
        mesh.polygons.foreach_set('material_index', np.asarray(self.material, dtype=np.int32))
        mesh.polygons.foreach_set('use_smooth', np.asarray(self.smooth))
        uv = mesh.uv_layers.new(name=old.uv_layers.active.name)
        uv.data.foreach_set('uv', np.asarray(self.uv, dtype=np.float32).ravel())
        uv.active_render, uv.active_clone = self.uv_flags
        self.obj.data = mesh
        # Blender stores the deform-group schema with the mesh data. Replacing
        # that data may empty obj.vertex_groups; restore the exact named order
        # before assigning any captured source or interpolated deform weights.
        self.obj.vertex_groups.clear()
        groups = [self.obj.vertex_groups.new(name=name) for name in self.group_names]
        assert [(group.index, group.name) for group in groups] == list(enumerate(self.group_names))
        for i in range(len(world)):
            weights = self.old_weights[i] if i < self.old_count else self.weights(i)
            for group, weight in weights.items():
                assert 0 <= group < len(groups)
                groups[group].add([i], weight, 'REPLACE')
        for vertex in mesh.vertices:
            actual_fields = {self.group_names[g.group]: g.weight for g in vertex.groups}
            expected_weights = self.old_weights[vertex.index] if vertex.index < self.old_count else self.weights(vertex.index)
            expected_fields = {self.group_names[g]: float(np.float32(w)) for g, w in expected_weights.items()}
            assert actual_fields == expected_fields, ('Named field restoration failed', self.obj.name, vertex.index)
        mesh.update()
        actual = A['points'](self.obj)[1]
        affected_faces = sorted(self.affected_faces-{-1})
        # Faces adjacent to a deformed retained vertex also belong to the local edit.
        touched = np.any(np.isin(self.base_faces, list(self.affected_vertices)), axis=1)
        affected_faces = np.union1d(affected_faces, np.flatnonzero(touched)).astype(np.int32)
        affected_corners = np.unique(self.base_corners[affected_faces])
        normals = np.empty((len(mesh.corner_normals), 3), dtype=np.float32)
        mesh.corner_normals.foreach_get('vector', normals.ravel())
        corner_source = np.asarray(self.corner_sources).ravel()
        unchanged_corners = (corner_source >= 0) & ~np.isin(corner_source, affected_corners)
        normals[unchanged_corners] = self.base_normals[corner_source[unchanged_corners]]
        mesh.normals_split_custom_set(normals.tolist())
        self.copy_attributes(old, mesh, corner_source, unchanged_corners)
        path = out/(self.obj.name+'-ancestry.npz')
        np.savez_compressed(path,
            vertexSourceIds=np.r_[np.arange(self.old_count, dtype=np.int32),
                                  np.full(len(world)-self.old_count, -1, dtype=np.int32)],
            vertexParentSourceIds=np.asarray(self.parents, dtype=np.int32),
            vertexParentCoefficients=np.asarray(self.coefficients, dtype=np.float32),
            faceSourceIds=np.asarray(self.face_sources, dtype=np.int32),
            cornerSourceIds=np.asarray(self.corner_sources, dtype=np.int32),
            affectedSourceVertices=np.array(sorted(self.affected_vertices), dtype=np.int32),
            affectedSourceFaces=affected_faces, affectedSourceCorners=affected_corners,
            authoredVertexRoles=np.asarray(self.vertex_roles, dtype=np.int8),
            authoredFaceRoles=np.asarray(self.face_roles, dtype=np.int8))
        report = {'ancestry': {'path': str(path.relative_to(ROOT)), 'sha256': sha(path)},
                  'sourceVertexCount': self.old_count, 'vertices': len(world),
                  'sourceTriangleCount': self.old_face_count, 'triangles': len(self.faces),
                  'newVertices': len(world)-self.old_count,
                  'vertexGroupNamesUnchanged': self.group_names,
                  'allSourcePrefixNamedFieldsExact': True,
                  'allNewSourceParentNamedFieldsExactAfterFloat32Storage': True,
                  'retainedSourceTriangles': int(np.sum(np.asarray(self.face_roles) == 0)),
                  'clippedSourceTriangles': int(np.sum(np.asarray(self.face_roles) == 1)),
                  'newLiningTriangles': int(np.sum(np.asarray(self.face_roles) == 2)),
                  'localRecompute': 'Normals recomputed only on affectedSourceCorners and new corners; all retained exterior corner normals and native attributes restored from source ancestry.',
                  'limits': 'Local surgery only; source prefix includes orphaned removed-cap vertices. Retained corner UVs exact; cuts interpolate source corners; new lining samples adjacent selected boundary UV. New fields interpolate source parents, normalize strongest four.'}
        return actual, np.asarray(self.faces, dtype=np.int32), report


def directed_boundary(surgery):
    """Return boundary half edges; coincident source UV seams are welded for incidence."""
    xyz = np.asarray(surgery.source)
    _, weld = np.unique(np.round(xyz, 8), axis=0, return_inverse=True)
    edges = defaultdict(list)
    for i, face in enumerate(surgery.faces):
        for k in range(3):
            a, b = face[k], face[(k+1) % 3]
            key = tuple(sorted((int(weld[a]), int(weld[b]))))
            if key[0] != key[1]:
                edges[key].append((i, k, a, b))
    return [rows[0] for rows in edges.values() if len(rows) == 1]


def lining(surgery, edges, axis, center, thickness, return_length, profile=None):
    """Turn the selected boundary inward, then extend the actual open lining."""
    unique = sorted({v for _, _, a, b in edges for v in (a, b)})
    rings = [{v: v for v in unique}]
    for amount, depth in ((thickness, 0.), (thickness, return_length)):
        ring = {}
        for v in unique:
            p = surgery.world[v]
            axial = float(np.sum((p-center)*axis))
            radial = p-center-axial*axis
            radius = np.linalg.norm(radial)
            assert radius > amount+1e-5
            target = center+(axial+depth)*axis+(radius-amount)*radial/radius
            if profile is not None:
                angle = np.arctan2(float(np.sum(radial*profile.z)), float(np.sum(radial*profile.x)))
                target_radius = float(profile.at(np.array([axial+depth]), np.array([angle]))[0])+0.0025
                target = center+(axial+depth)*axis+target_radius*radial/radius
            ring[v] = surgery.add(surgery.source[v], target, surgery.parents[v], surgery.coefficients[v], 3)
        rings.append(ring)
    for i, k, a, b in edges:
        uva, uvb = surgery.uv[i][k], surgery.uv[i][(k+1) % 3]
        third = surgery.uv[i][(k+2) % 3]
        for depth, (near, far) in enumerate(zip(rings[:-1], rings[1:])):
            # Sample a thin nondegenerate strip inside the actual adjacent source
            # UV triangle; new lining never invents a replacement palette.
            lo, hi = (0., .04) if depth == 0 else (.04, .16)
            na, nb = (1-lo)*uva+lo*third, (1-lo)*uvb+lo*third
            fa, fb = (1-hi)*uva+hi*third, (1-hi)*uvb+hi*third
            surgery.add_face([near[b], near[a], far[a]], [nb, na, fa], surgery.material[i])
            surgery.add_face([near[b], far[a], far[b]], [nb, fa, fb], surgery.material[i])
    return {'boundaryHalfEdges': len(edges), 'newInteriorVertices': len(unique)*2,
            'radialWallM': thickness, 'openReturnLengthM': return_length}


def source_sleeve_frame(original, controls, side):
    xyz = original*np.asarray(controls['sourceDisplayAffine']['scale'])+np.asarray(controls['sourceDisplayAffine']['translation'])
    bone = next(b for b in controls['authoringBones'] if b['name'] == 'AUTHOR_Forearm.'+side)
    head, tail = np.asarray(bone['sourceHead']), np.asarray(bone['sourceTail'])
    axis = unit(tail-head)
    u = unit(np.array([0., 0., 1.])-axis[2]*axis)
    v = np.cross(axis, u)
    delta = xyz-head
    s = np.sum(delta*axis, axis=1)
    radial = np.linalg.norm(delta-s[:, None]*axis, axis=1)
    own = xyz[:, 0] > 0 if side == 'L' else xyz[:, 0] < 0
    selected = own & (s > 0.4*np.linalg.norm(tail-head)) & (radial < .15)
    return xyz, head, axis, u, v, s, selected


def point_inside(point, polygon):
    a, b = polygon, np.roll(polygon, -1, axis=0)
    dy = b[:, 1]-a[:, 1]
    crossing_x = a[:, 0]+(point[1]-a[:, 1])*(b[:, 0]-a[:, 0])/np.where(dy != 0, dy, 1)
    return bool(np.sum(((a[:, 1] > point[1]) != (b[:, 1] > point[1])) & (point[0] < crossing_x)) % 2)


def polygon_ray_hits(polygon, direction):
    edge = np.roll(polygon, -1, axis=0)-polygon
    determinant = direction[0]*edge[:, 1]-direction[1]*edge[:, 0]
    valid = np.abs(determinant) > 1e-15
    inverse = 1/np.where(valid, determinant, 1)
    distance = (polygon[:, 0]*edge[:, 1]-polygon[:, 1]*edge[:, 0])*inverse
    fraction = (polygon[:, 0]*direction[1]-polygon[:, 1]*direction[0])*inverse
    hits = np.sort(distance[valid & (distance > 0) & (fraction >= 0) & (fraction <= 1)])
    assert len(hits), 'Ray from verified cavity center missed its actual owned polygon'
    return hits


def annular_hem(surgery, boundary, profile):
    """Constrained triangulation bridges the real inner/outer cut boundaries.

    Source vertex order remains intact, including non-star folds. No angular
    sorting or disk cap is used. CDT vertices must retain actual source points.
    """
    source = np.asarray(surgery.source)
    original_ids = sorted({v for _, _, a, b in boundary for v in (a, b)})
    _, inverse = np.unique(np.round(source[original_ids], 8), axis=0, return_inverse=True)
    representatives = {}
    for vertex, identity in zip(original_ids, inverse):
        representatives.setdefault(int(identity), vertex)
    native = np.array([representatives[i] for i in range(len(representatives))], dtype=np.int32)
    lookup = {vertex: int(identity) for vertex, identity in zip(original_ids, inverse)}
    edges = sorted({tuple(sorted((lookup[a], lookup[b]))) for _, _, a, b in boundary})
    graph = defaultdict(list)
    for a, b in edges:
        graph[a].append(b); graph[b].append(a)
    assert all(len(row) == 2 for row in graph.values())
    unseen, loops = set(graph), []
    while unseen:
        start = min(unseen); chain = [start]; previous, current = None, start
        while True:
            nxt = next(n for n in graph[current] if n != previous)
            if nxt == start:
                break
            assert nxt not in chain
            chain.append(nxt); previous, current = current, nxt
        unseen.difference_update(chain); loops.append(chain)
    assert len(loops) == 2, ('Expected two genuine cuff boundaries', len(loops))
    world = np.asarray(surgery.world)[native]
    axial = np.sum((world-profile.wrist)*profile.axis, axis=1)
    assert np.ptp(axial) < 2e-7, 'Mapped annular hem is not planar'
    planar = np.column_stack((np.sum((world-profile.wrist)*profile.x, axis=1),
                              np.sum((world-profile.wrist)*profile.z, axis=1)))
    areas = [abs(np.sum(planar[loop, 0]*np.roll(planar[loop, 1], -1)-planar[loop, 1]*np.roll(planar[loop, 0], -1)))/2 for loop in loops]
    outer_index = int(np.argmax(areas)); inner_index = 1-outer_index
    outer, inner = planar[loops[outer_index]], planar[loops[inner_index]]
    assert all(point_inside(p, outer) for p in inner), 'Mapped source annulus has lost containment'
    points_out, edges_out, triangles, vertex_origins, _, _ = delaunay_2d_cdt(
        [Vector(p) for p in planar], edges, [], 0, 1e-10, True)
    remap = []
    merged = 0
    for vertex, ancestry in zip(points_out, vertex_origins):
        assert ancestry, 'Crossed annular boundary created a CDT intersection point'
        if len(ancestry) > 1:
            assert all(np.array_equal(world[i].astype(np.float32), world[ancestry[0]].astype(np.float32)) for i in ancestry), 'CDT merged distinct source boundary points'
            merged += len(ancestry)-1
        remap.append(int(ancestry[0]))
    uv_at = {}
    for face_index, k, a, b in boundary:
        uv_at.setdefault(lookup[a], surgery.uv[face_index][k])
        uv_at.setdefault(lookup[b], surgery.uv[face_index][(k+1) % 3])
    kept = []
    for triangle in triangles:
        assert len(triangle) == 3
        ids = [remap[i] for i in triangle]
        centroid = planar[ids].mean(axis=0)
        if not point_inside(centroid, outer) or point_inside(centroid, inner):
            continue
        face = native[ids].tolist()
        normal = np.cross(world[ids[1]]-world[ids[0]], world[ids[2]]-world[ids[0]])
        if float(np.sum(normal*(-profile.axis))) < 0:
            ids.reverse(); face.reverse()
        surgery.add_face(face, [uv_at[i] for i in ids], surgery.material[boundary[0][0]])
        kept.append(face)
    assert kept
    # An annular face patch must expose both original rings and no new edge.
    counts = defaultdict(int)
    for face in kept:
        ids = [lookup[v] for v in face]
        for a, b in zip(ids, ids[1:]+ids[:1]):
            counts[tuple(sorted((a, b)))] += 1
    patch_boundary = {edge for edge, count in counts.items() if count == 1}
    assert patch_boundary == set(edges), 'Annular patch does not preserve every selected boundary edge'
    assert all(count <= 2 for count in counts.values())
    return {'sourceBoundaryLoops': 2, 'boundaryVertices': len(native), 'newAnnularTriangles': len(kept),
            'triangulation': 'Constrained actual planar boundaries; interior cavity triangles excluded',
            'sameFloat32PositionMerges': merged, 'everyOriginalBoundaryEdgePreserved': True,
            'innerCavityAreaM2': areas[inner_index], 'outerAreaM2': areas[outer_index]}


def contour_center(points, faces, face_sources, head, axis, u, v, station):
    """Find an interior point of the actual selected sleeve plane contour.

    Vertex-band bounding boxes are not contours and can put the origin outside
    a turned cuff. Only the triangle/plane intersection establishes this frame.
    Quantization joins diagnostic segment endpoints; source geometry is untouched.
    """
    scalar = np.sum((points-head)*axis, axis=1)-station
    distances = scalar[faces]
    active_ids = np.flatnonzero((distances.min(axis=1) <= 0) & (distances.max(axis=1) >= 0))
    segments, segment_sources = [], []
    for face_id in active_ids:
        face = faces[face_id]
        intersections = []
        for a, b in zip(face, np.roll(face, -1)):
            da, db = scalar[a], scalar[b]
            if da == 0:
                point = points[a]-head
                intersections.append([float(np.sum(point*u)), float(np.sum(point*v))])
            if da*db < 0:
                t = da/(da-db)
                point = points[a]+t*(points[b]-points[a])-head
                intersections.append([float(np.sum(point*u)), float(np.sum(point*v))])
        # A source vertex exactly on the plane is a real section endpoint.
        # The first station intentionally equals an actual source vertex s.
        intersections = list(dict.fromkeys(tuple(p) for p in intersections))
        assert len(intersections) <= 2, ('Coplanar source triangle needs explicit section handling', station, face.tolist())
        if len(intersections) == 2 and np.linalg.norm(np.subtract(*intersections)) > 1e-9:
            normal = np.cross(points[face[1]]-points[face[0]], points[face[2]]-points[face[0]])
            direction = np.cross(normal, axis)
            planar_direction = np.array([np.sum(direction*u), np.sum(direction*v)])
            if np.sum((np.asarray(intersections[1])-intersections[0])*planar_direction) < 0:
                intersections.reverse()
            segments.append(intersections); segment_sources.append(int(face_sources[face_id]))
    assert len(segments) >= 8, ('Insufficient actual source contour', station, len(segments))
    endpoints, indices = np.unique(np.round(np.asarray(segments).reshape(-1, 2), 8), axis=0, return_inverse=True)
    edge_segments = defaultdict(list)
    for index, (a, b) in enumerate(indices.reshape(-1, 2)):
        edge_segments[tuple(sorted((int(a), int(b))))].append(index)
    unique_edges = np.unique(np.sort(indices.reshape(-1, 2), axis=1), axis=0)
    unique_edges = unique_edges[unique_edges[:, 0] != unique_edges[:, 1]]
    adjacency = defaultdict(list)
    for a, b in unique_edges:
        adjacency[int(a)].append(int(b)); adjacency[int(b)].append(int(a))
    assert all(len(row) == 2 for row in adjacency.values()), ('Actual source contour is not closed', station,
        {'exactPlaneVertexIds': np.flatnonzero(scalar == 0)[:12].tolist(),
         'badEndpointDegrees': [(int(i), len(row), endpoints[i].tolist()) for i, row in adjacency.items() if len(row) != 2][:12]})
    unseen, loops, loop_sources, signed_areas = set(adjacency), [], [], []
    while unseen:
        first = min(unseen); chain = [first]; previous, current = None, first
        while True:
            following = next(n for n in adjacency[current] if n != previous)
            if following == first:
                break
            assert following not in chain
            chain.append(following); previous, current = current, following
        unseen.difference_update(chain); loops.append(endpoints[chain])
        member_segments = [i for a, b in zip(chain, chain[1:]+chain[:1]) for i in edge_segments[tuple(sorted((a, b)))]]
        oriented = np.asarray(segments)[member_segments]
        signed_areas.append(float(np.sum(oriented[:, 0, 0]*oriented[:, 1, 1]-oriented[:, 1, 0]*oriented[:, 0, 1])/2))
        loop_sources.append(sorted({segment_sources[i] for i in member_segments}))
    areas = [abs(np.sum(p[:, 0]*np.roll(p[:, 1], -1)-np.roll(p[:, 0], -1)*p[:, 1]))/2 for p in loops]
    assert len(loops) >= 2, ('Source sleeve lacks a measured cavity/exterior pair', station, areas)
    outer_index = int(np.argmax(areas)); outer = loops[outer_index]
    inner_candidates = [i for i, loop in enumerate(loops) if i != outer_index
                        and signed_areas[i]*signed_areas[outer_index] < 0
                        and all(point_inside(point, outer) for point in loop)]
    assert inner_candidates, ('No opposite-wound contained cavity contour', station, areas, signed_areas)
    inner_index = max(inner_candidates, key=lambda i: areas[i]); polygon = loops[inner_index]
    extra_loops = [{'loop': i, 'areaM2': areas[i], 'signedAreaM2FromSourceWinding': signed_areas[i],
                    'insideDominantOuter': all(point_inside(p, outer) for p in loop),
                    'insideDominantCavity': all(point_inside(p, polygon) for p in loop),
                    'sourceTriangleIds': loop_sources[i],
                    'treatment': 'Every source face and vertex retained; same positive map continues outside the dominant pair bearings; actual post-save geometry checks remain authoritative'}
                   for i, loop in enumerate(loops) if i not in (outer_index, inner_index)]
    cross = polygon[:, 0]*np.roll(polygon[:, 1], -1)-np.roll(polygon[:, 0], -1)*polygon[:, 1]
    assert abs(cross.sum()) > 1e-10
    centroid = np.sum((polygon+np.roll(polygon, -1, axis=0))*cross[:, None], axis=0)/(3*cross.sum())
    a, b = polygon, np.roll(polygon, -1, axis=0)
    edge = b-a
    def inside(point):
        crossings = ((a[:, 1] > point[1]) != (b[:, 1] > point[1]))
        denominator = b[:, 1]-a[:, 1]
        x = a[:, 0]+(point[1]-a[:, 1])*(b[:, 0]-a[:, 0])/np.where(abs(denominator) > 1e-20, denominator, 1)
        return bool(np.sum(crossings & (point[0] < x)) % 2)
    def clearance(point):
        t = np.clip(np.sum((point-a)*edge, axis=1)/np.sum(edge*edge, axis=1), 0, 1)
        return float(np.linalg.norm(point-a-t[:, None]*edge, axis=1).min())
    method = 'area centroid inside actual closed contour'
    if not inside(centroid) or clearance(centroid) < 1e-5:
        triangles = tessellate_polygon([[Vector((p[0], p[1], 0.)) for p in polygon]])
        candidates = [np.mean(np.asarray(triangle)[:, :2], axis=0) for triangle in triangles]
        candidates = [p for p in candidates if inside(p)]
        assert candidates, ('No triangulated interior point', station)
        centroid = max(candidates, key=clearance)
        method = 'verified interior triangle centroid with largest boundary clearance'
    assert inside(centroid) and clearance(centroid) > 1e-5
    return centroid, {'stationM': float(station), 'loops': len(loops), 'edges': len(polygon),
                      'interiorCenterUV': centroid.tolist(), 'minimumBoundaryDistanceM': clearance(centroid),
                      'exactPlaneVertexCount': int(np.sum(scalar == 0)), 'method': method,
                      'outerAreaM2': areas[outer_index], 'innerAreaM2': areas[inner_index],
                      'outerSignedAreaM2': signed_areas[outer_index], 'innerSignedAreaM2': signed_areas[inner_index],
                      'dominantOuterSourceTriangleIds': loop_sources[outer_index],
                      'dominantCavitySourceTriangleIds': loop_sources[inner_index],
                      'additionalClosedContours': extra_loops}, (outer, polygon)


def sleeve(surgery, controls, side, profile, settings):
    source = np.asarray(surgery.source)
    xyz, head, axis, u, v, s, selected = source_sleeve_frame(source, controls, side)
    tip = float(s[selected].max())
    section = settings['sourceTopology']['sides'][side]['sections'][7]
    assert section['closed'] and section['loopCount'] == 2
    cut = float(section['stationM'])
    f = np.asarray(surgery.faces)
    candidates = np.all(selected[f], axis=1)
    surgery.cut(s-cut, candidates)
    # The same positive cylindrical volume map moves all retained source folds.
    # Radius is NEVER treated as a source wall/layer ID.
    source = np.asarray(surgery.source)
    xyz, head, axis, u, v, s, selected = source_sleeve_frame(source, controls, side)
    lower = float(np.min(s[selected]))
    stations = np.linspace(lower, cut, 32)
    delta = xyz-head
    planar = np.column_stack((np.sum(delta*u, axis=1), np.sum(delta*v, axis=1)))
    local_faces = np.asarray(surgery.faces)
    local_mask = np.any(selected[local_faces], axis=1)
    local_sources = np.asarray(surgery.face_sources)[local_mask]
    local_faces = local_faces[local_mask]
    centers, section_receipts, source_contours = [], [], []
    for index, station in enumerate(stations):
        actual_station = station-1e-5 if index == len(stations)-1 else station
        center, receipt, contours = contour_center(xyz, local_faces, local_sources, head, axis, u, v, actual_station)
        centers.append(center); section_receipts.append(receipt); source_contours.append(contours)
    centers = np.asarray(centers)
    angles = np.arange(96)*2*np.pi/96
    inner_radii = np.empty((len(stations), len(angles)))
    outer_radii = np.empty_like(inner_radii)
    for i, (outer, inner) in enumerate(source_contours):
        for j, angle in enumerate(angles):
            direction = np.array([np.cos(angle), np.sin(angle)])
            ih = polygon_ray_hits(inner-centers[i], direction)
            oh = polygon_ray_hits(outer-centers[i], direction)
            # These are independently owned actual cavity/exterior contours.
            # Every folded portion between these bearings moves through the
            # same strictly increasing radius map; no vertex is assigned a wall
            # label from its radius or collapsed onto a fitted skin surface.
            inner_radii[i, j] = ih[0]
            outer_radii[i, j] = oh[-1]
    assert np.all(inner_radii > 0) and np.all(outer_radii-inner_radii > 1e-5)
    ids = np.flatnonzero(selected & (s <= cut+1e-7))
    center = np.column_stack([np.interp(s[ids], stations, centers[:, j]) for j in range(2)])
    offset = planar[ids]-center
    radius = np.linalg.norm(offset, axis=1)
    angle = np.arctan2(offset[:, 1], offset[:, 0])
    angular = np.mod(angle, 2*np.pi)*len(angles)/(2*np.pi)
    ia = np.floor(angular).astype(int) % len(angles); ib = (ia+1) % len(angles); ta = angular-np.floor(angular)
    upper = np.clip(np.searchsorted(stations, s[ids]), 1, len(stations)-1); lower_i = upper-1
    ts = np.clip((s[ids]-stations[lower_i])/(stations[upper]-stations[lower_i]), 0, 1)
    def lookup(radii):
        return (radii[lower_i, ia]*(1-ta)+radii[lower_i, ib]*ta)*(1-ts)+(radii[upper, ia]*(1-ta)+radii[upper, ib]*ta)*ts
    inner_radius, outer_radius = lookup(inner_radii), lookup(outer_radii)
    target_axis = -profile.axis
    target_u = unit(np.array([0., 0., 1.])-target_axis[2]*target_axis)
    target_v = np.cross(target_axis, target_u)
    direction = np.cos(angle)[:, None]*target_u+np.sin(angle)[:, None]*target_v
    body_angle = np.arctan2(np.sum(direction*profile.z, axis=1), np.sum(direction*profile.x, axis=1))
    native_station = settings['sleeveEndpointM']+(cut-s[ids])/(cut-stations[0])*(settings['sleeveTransitionM']-settings['sleeveEndpointM'])
    body_radius = profile.at(native_station, body_angle)
    radial_derivative = settings['sleeveWallM']/(outer_radius-inner_radius)
    assert np.all(radial_derivative > 0)
    radius_after = body_radius+settings['sleeveInnerEaseM']+(radius-inner_radius)*radial_derivative
    assert np.all(radius_after > 0), 'Actual annulus map reaches its axis'
    proposed = profile.wrist+native_station[:, None]*profile.axis+radius_after[:, None]*direction
    alpha = smooth((settings['sleeveTransitionM']-native_station)/(settings['sleeveTransitionM']-settings['sleeveFullM']))
    world = np.asarray(surgery.world)
    world[ids] += alpha[:, None]*(proposed-world[ids])
    surgery.move(world, ids[alpha > 0])
    edges = [e for e in directed_boundary(surgery) if abs(s[e[2]]-cut) < 1e-7 and abs(s[e[3]]-cut) < 1e-7]
    assert len(edges) > 30, ('No real sleeve opening', side, len(edges))
    result = annular_hem(surgery, edges, profile)
    return {'sourceCutAxialM': cut, 'sourceTipAxialM': tip, 'newHem': result,
            'cutChoice': 'Rebuild at last measured genuine annulus, source section7. The distal turned/oblique lip is removed, not mislabeled a sealed cap. Parent must judge selected cuff detail loss. Both actual source walls before the plane remain.',
            'removedSourceAxialLengthM': float(tip-cut),
            'positiveRadiusScaleRange': [float(np.min(radius_after/radius)), float(np.max(radius_after/radius))],
            'sourceRadialMeaning': 'One positive radius map over the actual material domain, bounded by separately owned nested cavity/exterior polygons; folds retain their vertices/faces and distinct radii. Analytic positivity does not waive dense triangle crossing checks.',
            'radialMapDerivativeRange': [float(radial_derivative.min()), float(radial_derivative.max())],
            'sourceSectionCenters': section_receipts}


def floor_cut(surgery, guide, plane):
    source = np.asarray(surgery.source)
    f = np.asarray(surgery.faces)
    surgery.cut(source[:, 1]-plane, np.ones(len(f), dtype=bool), keep_both=True)
    source = np.asarray(surgery.source)
    edges = defaultdict(list)
    for i, face in enumerate(surgery.faces):
        for k in range(3):
            a, b = face[k], face[(k+1) % 3]
            edges[tuple(sorted((a, b)))].append(i)
    plane_edges = {e for e in edges if abs(source[e[0], 1]-plane) < 1e-7 and abs(source[e[1], 1]-plane) < 1e-7}
    adj = defaultdict(list)
    for a, b in plane_edges:
        adj[a].append(b); adj[b].append(a)
    assert all(len(n) == 2 for n in adj.values()), 'Cut section is not a family of simple loops'
    loops = []
    unseen = set(adj)
    while unseen:
        start = min(unseen); chain = [start]; previous = None; at = start
        while True:
            nxt = next(n for n in adj[at] if n != previous)
            if nxt == start:
                break
            assert nxt not in chain
            chain.append(nxt); previous, at = at, nxt
        unseen.difference_update(chain); loops.append(chain)
    center = V['polygon_center'](guide['section2_loop1_originalXYZ'])
    def loop_score(loop):
        points = source[loop][:, [0, 2]]
        area = abs(np.sum(points[:, 0]*np.roll(points[:, 1], -1)-points[:, 1]*np.roll(points[:, 0], -1)))/2
        return area
    # At source Y=-.65 the cavity and exterior are the two recorded loops.
    assert len(loops) == 2, ('Unexpected dense cut loop count; do not guess floor', len(loops))
    chosen = min(loops, key=loop_score)
    assert np.linalg.norm(source[chosen][:, [0, 2]].mean(axis=0)-center) < .1
    barrier = {tuple(sorted((a, b))) for a, b in zip(chosen, chosen[1:]+chosen[:1])}
    seeds = [i for e in barrier for i in edges[e] if source[surgery.faces[i], 1].mean() > plane+1e-9]
    adjacency = defaultdict(list)
    for e, rows in edges.items():
        if e not in barrier and len(rows) == 2:
            a, b = rows; adjacency[a].append(b); adjacency[b].append(a)
    reached = set(seeds); todo = deque(seeds)
    while todo:
        for other in adjacency[todo.popleft()]:
            if other not in reached:
                reached.add(other); todo.append(other)
    assert 10 < len(reached) < .18*len(surgery.faces), ('Floor component escaped interior', len(reached), len(surgery.faces))
    surgery.delete(reached)
    boundary = directed_boundary(surgery)
    assert len(boundary) == len(chosen), ('Unexpected open glove boundaries', len(boundary), len(chosen))
    return boundary, {'sourceFloorCutY': plane, 'deletedInteriorTriangles': len(reached),
                      'innerBoundaryVertices': len(chosen), 'sourceSectionLoops': len(loops)}


def glove(surgery, dump, placement, profile, settings):
    boundary, report = floor_cut(surgery, dump, settings['gloveFloorCutY'])
    scale, basis_x, basis_z = V['cuff_frame'](dump, placement)
    source = np.asarray(surgery.source)
    before = np.asarray(surgery.world)
    axial, x, z = V['source_cuff'](source, dump, settings['sourceWrist'], scale, basis_x, basis_z)
    # One positive affine cross-section fits both actual complete inner loops.
    # This retains cuff wall/band/lip relationships instead of compressing them.
    required = 1.
    for sec in (2, 3):
        polygon = dump[f'section{sec}_loop1_originalXYZ']
        p = polygon[:, [0, 2]]-V['polygon_center'](polygon)
        for angle in np.arange(96)*2*np.pi/96:
            direction = np.array([np.cos(angle), np.sin(angle)])
            edge = np.roll(p, -1, axis=0)-p
            det = direction[0]*edge[:, 1]-direction[1]*edge[:, 0]
            valid = np.abs(det) > 1e-14
            inv = 1/np.where(valid, det, 1)
            distance = (p[:, 0]*edge[:, 1]-p[:, 1]*edge[:, 0])*inv
            fraction = (p[:, 0]*direction[1]-p[:, 1]*direction[0])*inv
            hits = distance[valid & (distance > 0) & (fraction >= 0) & (fraction <= 1)]
            assert len(hits)
            station = (settings['sourceWrist'][1]-float(polygon[0, 1]))*scale
            need = float(profile.at(np.array([station]), np.array([angle]))[0])+settings['gloveCavityEaseM']
            required = max(required, need/(hits.min()*scale))
    assert required <= settings['maximumCuffScale'], ('Full-angle source cuff fit exceeds selected identity bound', required)
    proposed = profile.wrist+axial[:, None]*profile.axis+required*x[:, None]*basis_x+required*z[:, None]*basis_z
    alpha = smooth((settings['gloveJoinY']-source[:, 1])/(settings['gloveJoinY']-settings['gloveFullY']))
    result = before+alpha[:, None]*(proposed-before)
    surgery.move(result, np.flatnonzero(alpha > 0))
    # The old cavity floor is physically gone. The new lining continues toward
    # the anatomical wrist; its open distal end sits inside the selected hand.
    inner = lining(surgery, boundary, profile.axis, profile.wrist, .0008,
                   -settings['gloveLiningLengthM'], profile=profile)
    report.update(sourceTransverseUniformScale=required, newLining=inner,
                  fitSampling='96 directions at each of two actual inner cavity planes; axial-overlap validity remains subject to actual triangle checks, not inferred from these bearings')
    return report


def main():
    global V, A
    args = sys.argv[sys.argv.index('--')+1:]
    assert len(args) == 1
    out = Path(args[0]).resolve()
    assert out.is_relative_to(ROOT/'harness/out/rider-rebuild/astra-character-construction12') and not out.exists()
    config = json.loads((HERE/'input.json').read_text())
    V = runpy.run_path(str(pin(config['volumeHelper'])))
    A = runpy.run_path(str(pin(config['intersectionHelper'])))
    prior = json.loads(pin(config['priorInputs']).read_text())
    for name in ('master', 'originalGloveDense', 'originalHoodie', 'placement', 'hoodieSourceFrames', 'restHelper', 'geometryHelper'):
        pin(prior[name])
    for row in prior['guideArrays'].values():
        pin(row)
    source_glove = np.load(pin(prior['originalGloveDense']))['vertices']
    source_hoodie = V['read_hoodie'](pin(prior['originalHoodie']))
    placement = json.loads(pin(prior['placement']).read_text())
    controls = json.loads(pin(prior['hoodieSourceFrames']).read_text())
    bpy.ops.wm.open_mainfile(filepath=str(pin(prior['master'])))
    rig = bpy.data.objects['RiderSkeleton']
    assert len(rig.data.bones) == 75 and all(b.matrix_basis.is_identity for b in rig.pose.bones)
    assert {o.name for o in bpy.context.scene.objects if o.type == 'MESH' and not o.hide_render} == VISIBLE
    rest = runpy.run_path(str(pin(prior['restHelper'])))['rest']
    geometry = runpy.run_path(str(pin(prior['geometryHelper'])))['geometry']
    protected = [bpy.data.objects[n] for n in (VISIBLE-set(EDITED)) | {'RiderBody__FullAnatomyReference'}]
    protected_before = {o.name: geometry(o) for o in protected}
    rest_before = rest(rig)
    out.mkdir(parents=True)
    settings = dict(config['settings'])
    settings['sourceTopology'] = json.loads(pin(config['sourceTopology']).read_text())
    settings['sourceWrist'] = placement['sourceRest']['wrist']
    body = bpy.data.objects['RiderBody__FullAnatomyReference']
    _, bp = A['points'](body); bf = A['faces'](body)
    profiles, dumps = {}, {}
    for side in ('L', 'R'):
        dump = np.load(pin(prior['guideArrays'][side])); dumps[side] = dump
        _, x, z = V['cuff_frame'](dump, placement['hands'][side])
        profile_settings = {'bodyProfileStations': 49, 'bodyProfileAngles': 96}
        profile = V['BodyProfile'](bp, bf, dump['wristWorld'], dump['forearmAxisWorld'], x, z, profile_settings)
        # Extend actual anatomical sampling into the full forearm transition.
        profile.stations = np.linspace(-.015, .19, 49)
        local = np.sum((bp-profile.wrist)*profile.axis, axis=1)
        crop = bf[np.any((local[bf] > -.035) & (local[bf] < .21), axis=1)]
        bvh = tree(bp, crop)
        for i, station in enumerate(profile.stations):
            for j, angle in enumerate(profile.angles):
                direction = np.cos(angle)*x+np.sin(angle)*z
                hit = hit_radius(bvh, profile.wrist+station*profile.axis, direction)
                assert hit is not None, ('Actual anatomy profile miss', side, station, angle)
                profile.radii[i, j] = hit
        profiles[side] = profile
    report = {'acceptedArt': False, 'status': 'UNACCEPTED_LOCAL_GEOMETRY_CONSTRUCTION',
              'sourceMaster': prior['master'], 'visibleMeshes': sorted(VISIBLE), 'objects': {}, 'hands': {},
              'recipeSHA256': sha(__file__), 'inputSHA256': sha(HERE/'input.json'),
              'newTopology': 'Selected sleeve distal-lip truncation at measured true annulus, positive mapping of both retained walls, actual annular hem; selected glove internal-floor deletion and source-parent lining',
              'geometryGatesPassed': False, 'movingReviewPassed': False}
    hoodie = Surgery(bpy.data.objects['RiderHoodie'], source_hoodie)
    for side in ('L', 'R'):
        print('CONSTRUCT sleeve '+side, flush=True)
        report['hands'][side] = {'sleeve': sleeve(hoodie, controls, side, profiles[side], settings)}
    report['sleeveRemovedDegenerates'] = hoodie.remove_degenerates()
    hp, hf, row = hoodie.finish(out); report['objects']['RiderHoodie'] = row
    actual = {}
    for side in ('L', 'R'):
        print('CONSTRUCT glove '+side, flush=True)
        surgery = Surgery(bpy.data.objects['ActualSelectedGlove.'+side], source_glove)
        report['hands'][side]['glove'] = glove(surgery, dumps[side], placement['hands'][side], profiles[side], settings)
        report['hands'][side]['removedDegenerates'] = surgery.remove_degenerates()
        gp, gf, row = surgery.finish(out); report['objects'][surgery.obj.name] = row
        actual[side] = (gp, gf)
    assert protected_before == {o.name: geometry(o) for o in protected}
    assert rest_before == rest(rig)
    report['exact75RestUnchanged'] = True
    report['protectedGeometryUnchanged'] = protected_before
    native = out/'UNACCEPTED-complete-selected-rider.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(native), compress=True)
    report['native'] = {'path': str(native.relative_to(ROOT)), 'sha256': sha(native)}
    report_path = out/'construction.json'
    report_path.write_text(json.dumps(report, indent=2)+'\n')
    # Save the actual full model first; every failure remains explicitly failed.
    visible_body = bpy.data.objects['RiderBody']
    _, vp = A['points'](visible_body); vf = A['faces'](visible_body)
    for side in ('L', 'R'):
        profile = profiles[side]; gp, gf = actual[side]
        ga = np.sum((gp-profile.wrist)*profile.axis, axis=1)
        ha = np.sum((hp-profile.wrist)*profile.axis, axis=1)
        va = np.sum((vp-profile.wrist)*profile.axis, axis=1)
        gx = (gp[:, 0] > 0) if side == 'L' else (gp[:, 0] < 0)
        hx = (hp[:, 0] > 0) if side == 'L' else (hp[:, 0] < 0)
        vx = (vp[:, 0] > 0) if side == 'L' else (vp[:, 0] < 0)
        gc = gf[np.any((gx & (ga > -.018) & (ga < .1))[gf], axis=1)]
        hc = hf[np.any((hx & (ha > -.005) & (ha < .195))[hf], axis=1)]
        vc = vf[np.any((vx & (va > -.02) & (va < .20))[vf], axis=1)]
        checks = [('gloveSelf', lambda: A['intersections'](gp, gc)),
                  ('sleeveSelf', lambda: A['intersections'](hp, hc)),
                  ('gloveSleeve', lambda: A['intersections'](gp, gc, hp, hc)),
                  ('gloveVisibleWearer', lambda: A['intersections'](gp, gc, vp, vc)),
                  ('sleeveVisibleWearer', lambda: A['intersections'](hp, hc, vp, vc))]
        report['hands'][side]['geometry'] = {}
        for name, check in checks:
            print('CHECK '+side+' '+name, flush=True)
            report['hands'][side]['geometry'][name] = check()
            report_path.write_text(json.dumps(report, indent=2)+'\n')
    report['geometryGatesPassed'] = all(row['passed'] for hand in report['hands'].values() for row in hand['geometry'].values())
    report['status'] = 'UNACCEPTED_MOVING_REVIEW_PENDING' if report['geometryGatesPassed'] else 'REJECTED_LOCAL_GEOMETRY_REQUIRES_CORRECTION'
    report_path.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'native': report['native'], 'status': report['status']}), flush=True)


if __name__ == '__main__':
    main()
