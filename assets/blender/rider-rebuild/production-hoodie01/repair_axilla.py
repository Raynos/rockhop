"""One concrete regional repair: clean face fans, directly author quad grids.

Source-only until checkpoint/lease. Same arguments as the frozen author.py.
This changes local cut selection; it is a shape/topology repair, not another
selection-setting trial. No grid-fill operator or garment-wide solver is used.
"""
import hashlib
import json
import runpy
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

BASE = Path(__file__).with_name('author.py')
BASE_SHA = '078da52b40e1f5049759314c1794ba6559ac1dae90d79294672c674f2095d14a'


def rebuild_axilla(obj, spec, targets, diagnostics):
    namespace = rebuild_axilla.base_globals
    fit_point = namespace['fit_point']
    boundary_cycles = namespace['boundary_cycles']
    collar = fit_point(Vector(spec['protectedPorts']['sourceCollarCenterM']), spec, targets)[0]

    def port(edge):
        p = sum((v.co for v in edge.verts), Vector())/2
        c = spec['protectedPorts']
        if abs(p.z-spec['targetHemZ']) < c['hemSlabHalfWidthM']: return True
        if sum(((p[i]-collar[i])/c['collarRadiiM'][i])**2 for i in range(3)) < 1: return True
        for _, elbow, wrist in targets.values():
            axis = (wrist-elbow).normalized()
            axial = (p-wrist).dot(axis)
            if abs(axial) < c['cuffSlabHalfWidthM'] and (p-wrist-axis*axial).length < c['cuffRadiusM']:
                return True
        return False

    receipts = []
    obj.data.attributes.new('_HOODIE_PATCH', 'INT', 'FACE')
    for side, center in spec['axillaPatch']['centers'].items():
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bm.verts.ensure_lookup_table()
        bm.verts.index_update()
        original_boundary = {edge for edge in bm.edges if edge.is_boundary}
        protected = {edge for edge in original_boundary if port(edge)}
        center = Vector(center)
        radius = Vector(spec['axillaPatch']['radiiM'])
        chosen = {f for f in bm.faces
                  if sum(((f.calc_center_median()[i]-center[i])/radius[i])**2 for i in range(3)) < 1}
        assert chosen, ('Empty regional underarm repair', side)
        seed_count = len(chosen)
        # An ellipse can select alternating sectors around one source vertex.
        # Expand only those pinched local face fans, making the authored cut a
        # true mesh perimeter rather than several disks touching at a vertex.
        expanded = set()
        for iteration in range(8):
            retained_boundary = {e for e in bm.edges
                                 if sum(f not in chosen for f in e.link_faces) == 1}
            local = {e for e in retained_boundary if e not in protected
                     and (e not in original_boundary or
                          sum((((e.verts[0].co[i]+e.verts[1].co[i])/2-center[i])/radius[i])**2
                              for i in range(3)) < 1.25**2)}
            nearby = {v for e in local for v in e.verts}
            pinches = [v for v in nearby if sum(e in retained_boundary for e in v.link_edges) > 2]
            if not pinches: break
            additions = {f for v in pinches for f in v.link_faces}-chosen
            assert additions and not any(e in protected for f in additions for e in f.edges), \
                ('Local fan repair reached a genuine garment aperture', side)
            chosen.update(additions)
            expanded.update(additions)
        else:
            raise AssertionError(('Regional fan repair needs a manually redrawn perimeter', side))
        assert not any(e in protected for f in chosen for e in f.edges)
        # Selection expansion is disclosed and bounded to this local cut. It
        # deliberately absorbs generated tears; original topology is not sacred.
        bmesh.ops.delete(bm, geom=list(chosen), context='FACES')
        candidates = {e for e in bm.edges if e.is_boundary and e not in protected
                      and (e not in original_boundary or
                           sum((((e.verts[0].co[i]+e.verts[1].co[i])/2-center[i])/radius[i])**2
                               for i in range(3)) < 1.25**2)}
        stack = list(candidates)
        while stack:
            for v in stack.pop().verts:
                for edge in v.link_edges:
                    if edge.is_boundary and edge not in protected and edge not in candidates:
                        candidates.add(edge)
                        stack.append(edge)
        cycles = boundary_cycles(candidates)
        for cycle in cycles:
            if len(cycle) % 2:
                edge = next(e for e in cycle[0].link_edges if cycle[1] in e.verts)
                bmesh.ops.subdivide_edges(bm, edges=[edge], cuts=1, use_grid_fill=False)
        candidates = {e for e in bm.edges if e.is_boundary and e not in protected
                      and (e not in original_boundary or
                           sum((((e.verts[0].co[i]+e.verts[1].co[i])/2-center[i])/radius[i])**2
                               for i in range(3)) < 1.25**2)}
        stack = list(candidates)
        while stack:
            for v in stack.pop().verts:
                for edge in v.link_edges:
                    if edge.is_boundary and edge not in protected and edge not in candidates:
                        candidates.add(edge)
                        stack.append(edge)
        cycles = boundary_cycles(candidates)
        patch = bm.faces.layers.int.get('_HOODIE_PATCH')
        assert patch is not None
        created = []
        for cycle in cycles:
            assert len(cycle) >= 8 and len(cycle) % 2 == 0
            edge = next(e for e in cycle[0].link_edges if cycle[1] in e.verts)
            if edge.link_loops[0].vert == cycle[0]: cycle = list(reversed(cycle))
            width = len(cycle)//4
            height = len(cycle)//2-width
            grid = {}
            perimeter = ([(0, j) for j in range(width+1)]
                         +[(i, width) for i in range(1, height+1)]
                         +[(height, j) for j in range(width-1, -1, -1)]
                         +[(i, 0) for i in range(height-1, 0, -1)])
            assert len(perimeter) == len(cycle)
            for key, vertex in zip(perimeter, cycle): grid[key] = vertex
            top = [grid[0, j].co.copy() for j in range(width+1)]
            bottom = [grid[height, j].co.copy() for j in range(width+1)]
            left = [grid[i, 0].co.copy() for i in range(height+1)]
            right = [grid[i, width].co.copy() for i in range(height+1)]
            for i in range(1, height):
                t = i/height
                for j in range(1, width):
                    u = j/width
                    bilinear = ((1-t)*(1-u)*top[0]+(1-t)*u*top[-1]
                                +t*(1-u)*bottom[0]+t*u*bottom[-1])
                    position = (1-t)*top[j]+t*bottom[j]+(1-u)*left[i]+u*right[i]-bilinear
                    grid[i, j] = bm.verts.new(position)
            for i in range(height):
                for j in range(width):
                    face = bm.faces.new((grid[i, j], grid[i, j+1], grid[i+1, j+1], grid[i+1, j]))
                    face[patch] = 1 if side == 'L' else 2
                    face.smooth = True
                    created.append(face)
            bm.normal_update()
            for i in range(1, height):
                for j in range(1, width):
                    vertex = grid[i, j]
                    vertex.co += vertex.normal*spec['axillaPatch']['sculptFullnessM']
        assert created and all(len(f.verts) == 4 for f in created)
        bm.normal_update()
        record = {'side': side, 'method': 'Direct welded perimeter quad grids; no fill operator',
                  'ellipseSeedFaces': seed_count, 'expandedPinchedFanFaces': len(expanded),
                  'removedFaces': seed_count+len(expanded),
                  'boundarySizes': [len(c) for c in cycles], 'authoredQuads': len(created),
                  'shapeSelectionChanged': bool(expanded), 'actualAddedNonQuads': 0}
        diagnostics.append(record)
        receipts.append(record)
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        bm.to_mesh(obj.data)
        bm.free()
        obj.data.update()
    return receipts


def main():
    assert hashlib.sha256(BASE.read_bytes()).hexdigest() == BASE_SHA, 'Frozen base author changed'
    loaded = runpy.run_path(str(BASE))
    globals_ = loaded['main'].__globals__
    globals_['rebuild_axilla'] = rebuild_axilla
    globals_['__file__'] = str(Path(__file__).resolve())
    rebuild_axilla.base_globals = globals_
    globals_['main']()


if __name__ == '__main__': main()
