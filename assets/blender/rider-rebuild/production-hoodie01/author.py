"""Conventional selected25 proportional fit, authored axilla patches and bake.

Parent checkpoints this source and grants a bounded serial CPU2 lease first.
blender -b -t 2 --python-exit-code 1 --python author.py -- inputs.json OUT author
blender -b -t 2 --python-exit-code 1 --python author.py -- inputs.json OUT bake AUTHOR
Each OUT must be fresh under harness/out/rider-rebuild/production-hoodie01/.
No original edit, source-rig authority, solver, body hiding or player export.
"""
import hashlib
import json
import math
import sys
from pathlib import Path

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.kdtree import KDTree

ROOT = Path(__file__).resolve().parents[4]
SOURCE_KEYS = ('selectedNative', 'originalDensePaint', 'nativeMaster',
               'nativeArrays', 'geometricControlReceipt')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def active(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.hide_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def smooth(a, b, x):
    t = max(0., min(1., (x-a)/(b-a)))
    return t*t*(3-2*t)


def signature(body, rig):
    state = {'vertices': [list(v.co) for v in body.data.vertices],
             'polygons': [list(f.vertices) for f in body.data.polygons],
             'groups': [g.name for g in body.vertex_groups],
             'weights': [[[g.group, g.weight] for g in v.groups]
                         for v in body.data.vertices],
             'bones': [[b.name, list(b.head_local), list(b.tail_local),
                        [list(r) for r in b.matrix_local]] for b in rig.data.bones]}
    return hashlib.sha256(json.dumps(state, separators=(',', ':')).encode()).hexdigest()


def hoodie_geometry(obj):
    return hashlib.sha256(json.dumps({'vertices': [list(v.co) for v in obj.data.vertices],
                                     'polygons': [list(f.vertices) for f in obj.data.polygons]},
                                    separators=(',', ':')).encode()).hexdigest()


def target_arms(rig):
    return {side: [rig.data.bones['DEF-upper_arm.'+side].head_local.copy(),
                   rig.data.bones['DEF-forearm.'+side].head_local.copy(),
                   rig.data.bones['DEF-hand.'+side].head_local.copy()]
            for side in ('L', 'R')}


def sleeve_edit(p, source, target, radial_scale, blend_range, radius, elbow_width):
    """Ordinary proportional brush ownership around an authored arm axis.

    An axial interval and a radial brush radius define the sleeve falloff.
    The hood is outside the brush; lateral position alone never owns an arm.
    """
    mapped, distances = [], []
    for a, b, c, d in zip(source, source[1:], target, target[1:]):
        axis, new_axis = b-a, d-c
        fraction = (p-a).dot(axis)/axis.length_squared
        center = a+axis*fraction
        finite_center = a+axis*max(0., min(1., fraction))
        distances.append((p-finite_center).length)
        rotation = axis.normalized().rotation_difference(new_axis.normalized())
        mapped.append(c+new_axis*fraction+(rotation @ (p-center))*radial_scale)
    axis = (source[1]-source[0]).normalized()
    along = (p-source[0]).dot(axis)
    radial = min(distances)
    upper_length = (source[1]-source[0]).length
    elbow = smooth(upper_length-elbow_width, upper_length+elbow_width, along)
    influence = smooth(*blend_range, along)*(1-smooth(radius, radius*1.35, radial))
    return mapped[0].lerp(mapped[1], elbow), influence


def fit_point(p, spec, targets, dense=False):
    hem = spec['targetHemZ']
    shoulder = sum(a[0].z for a in targets.values())/2
    zscale = (shoulder-hem)/(spec['sourceShoulderZ']-spec['sourceHemZ'])
    if dense:
        control = spec['denseDisplayTorso']
        old_torso = Vector((p.x*control['lateralScale']+control['centerX'],
                            p.y*control['depthScale'],
                            p.z*control['heightScale']+control['up']))
        arms = spec['denseDisplayArms']
        radial_scale = spec['denseRadialScale']
        blend = spec['denseArmholeBlendAlongM']
        radius = spec['denseArmholeInfluenceRadiusM']
        elbow_width = .13
    else:
        old_torso = p
        arms = spec['sourceArms']
        radial_scale = spec['armRadialScale']
        blend = spec['armholeBlendAlongM']
        radius = spec['armholeInfluenceRadiusM']
        elbow_width = spec['elbowBlendHalfWidthM']
    # Fit thorax/hem. Preserve selected hood height and folds above shoulder.
    z = hem+(old_torso.z-spec['sourceHemZ'])*zscale
    if old_torso.z > spec['sourceShoulderZ']:
        z = shoulder+old_torso.z-spec['sourceShoulderZ']
    torso = Vector((old_torso.x*spec['torsoRadialScale'],
                    old_torso.y*spec['torsoRadialScale'], z))
    # Separate left/right brush volumes, never a torso/sleeve abs(X) threshold.
    edits = []
    for side in ('L', 'R'):
        source = [Vector(a) for a in arms[side]]
        point, alpha = sleeve_edit(p, source, targets[side], radial_scale,
                                   blend, radius, elbow_width)
        edits.append((alpha, side, point))
    alpha, side, point = max(edits, key=lambda row: row[0])
    return torso.lerp(point, alpha), side, alpha


def boundary_cycles(edges):
    remaining = set(edges)
    result = []
    while remaining:
        first = min(remaining, key=lambda e: e.index)
        start, current = first.verts
        cycle = [start]
        previous = first
        remaining.remove(first)
        while current != start:
            cycle.append(current)
            choices = [e for e in current.link_edges if e in remaining]
            assert len(choices) == 1, ('Axilla cut is not a simple disk boundary',
                                       len(choices), list(current.co))
            previous = choices[0]
            remaining.remove(previous)
            current = previous.other_vert(current)
        result.append(cycle)
    return result


def rebuild_axilla(obj, spec, targets):
    """Replace two local underarm regions; Blender grid fill authors quad loops.

    Only authored sleeve/collar/hem aperture regions are protected. Existing
    generated underarm holes join the cut and its welded grid patch. A cut
    touching a real port or branching boundary fails instead of being capped.
    """
    receipts = []
    patch = obj.data.attributes.new('_HOODIE_PATCH', 'INT', 'FACE')
    collar_center = fit_point(Vector(spec['protectedPorts']['sourceCollarCenterM']),
                             spec, targets)[0]

    def port(edge):
        p = (edge.verts[0].co+edge.verts[1].co)/2
        controls = spec['protectedPorts']
        if abs(p.z-spec['targetHemZ']) < controls['hemSlabHalfWidthM']:
            return 'hem'
        if sum(((p[j]-collar_center[j])/controls['collarRadiiM'][j])**2
               for j in range(3)) < 1:
            return 'collar'
        for side, (_, elbow, wrist) in targets.items():
            axis = (wrist-elbow).normalized()
            axial = (p-wrist).dot(axis)
            radial = (p-wrist-axis*axial).length
            if (abs(axial) < controls['cuffSlabHalfWidthM'] and
                    radial < controls['cuffRadiusM']):
                return 'cuff.'+side
        return None

    for side, center in spec['axillaPatch']['centers'].items():
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        original_boundary = {e for e in bm.edges if e.is_boundary}
        protected = {e for e in original_boundary if port(e) is not None}
        center = Vector(center)
        radii = Vector(spec['axillaPatch']['radiiM'])
        chosen = [f for f in bm.faces
                  if sum(((f.calc_center_median()[j]-center[j])/radii[j])**2
                         for j in range(3)) < 1]
        assert chosen, ('Empty authored underarm region', side)
        assert not any(e in protected for f in chosen for e in f.edges), \
            ('Authored underarm patch touches a genuine garment port', side)
        count = len(chosen)
        bmesh.ops.delete(bm, geom=chosen, context='FACES')

        def patch_edges():
            # Include existing generated holes connected to the authored cut.
            # This is local mesh editing, not a garment-wide port classifier.
            found = {e for e in bm.edges if e.is_boundary and e not in protected
                     and (e not in original_boundary or
                          sum((((e.verts[0].co[j]+e.verts[1].co[j])/2-center[j])/radii[j])**2
                              for j in range(3)) < 1.25**2)}
            stack = list(found)
            while stack:
                edge = stack.pop()
                for vertex in edge.verts:
                    for other in vertex.link_edges:
                        if other.is_boundary and other not in protected and other not in found:
                            found.add(other)
                            stack.append(other)
            return list(found)

        cuts = patch_edges()
        # Grid fill needs even boundary counts; split one edge when needed.
        cycles = boundary_cycles(cuts)
        for cycle in cycles:
            if len(cycle) % 2:
                edge = next(e for e in cycle[0].link_edges if cycle[1] in e.verts)
                bmesh.ops.subdivide_edges(bm, edges=[edge], cuts=1, use_grid_fill=False)
        bm.edges.index_update()
        cuts = patch_edges()
        cycles = boundary_cycles(cuts)
        bm.verts.index_update()
        indices = [[v.index for v in cycle] for cycle in cycles]
        bm.to_mesh(obj.data)
        bm.free()
        generated = 0
        for ids in indices:
            active(obj)
            bpy.context.tool_settings.mesh_select_mode = (False, True, False)
            for v in obj.data.vertices: v.select = False
            for e in obj.data.edges: e.select = False
            for f in obj.data.polygons: f.select = False
            selected = set(ids)
            for edge in obj.data.edges:
                if set(edge.vertices).issubset(selected): edge.select = True
            bpy.ops.object.mode_set(mode='EDIT')
            result = bpy.ops.mesh.fill_grid(span=max(1, len(ids)//4), offset=0,
                                            use_interp_simple=False)
            bpy.ops.object.mode_set(mode='OBJECT')
            assert result == {'FINISHED'}, ('Blender quad-grid fill failed', side)
            # Reacquire attributes after edit operations; RNA can be replaced.
            patch = obj.data.attributes.get('_HOODIE_PATCH')
            assert patch is not None
            new_faces = [f for f in obj.data.polygons if f.select]
            assert new_faces and all(len(f.vertices) == 4 for f in new_faces), \
                ('Axilla grid did not create quad deformation loops', side)
            for face in new_faces:
                patch.data[face.index].value = 1 if side == 'L' else 2
                face.use_smooth = True
                generated += 1
            vertices = {i for f in new_faces for i in f.vertices}-selected
            # Deliberate cotton fullness across the new quad patch, with the
            # welded perimeter fixed. Ordinary sculpt offset, not a fit solver.
            obj.data.update()
            for i in vertices:
                vertex = obj.data.vertices[i]
                vertex.co += vertex.normal*spec['axillaPatch']['sculptFullnessM']
        receipts.append({'side': side, 'removedFaces': count,
                         'boundarySizes': [len(ids) for ids in indices],
                         'authoredQuads': generated})
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    return receipts


def skin(obj, body, rig, spec, targets):
    names = {g.index: g.name for g in body.vertex_groups}
    fields = [{names[g.group]: g.weight for g in v.groups if g.weight > 0}
              for v in body.data.vertices]
    scopes = {'torso': lambda n: n.startswith('DEF-spine') and n not in
              ('DEF-spine.005', 'DEF-spine.006')}
    for side in ('L', 'R'):
        scopes[side] = lambda n, side=side: any(n.startswith('DEF-'+a+'.'+side)
                                              for a in ('shoulder', 'upper_arm', 'forearm'))
    trees = {}
    for region, allowed in scopes.items():
        ids = [v.index for v, row in zip(body.data.vertices, fields)
               if sum(w for n, w in row.items() if allowed(n)) > .55]
        tree = KDTree(len(ids))
        for i in ids: tree.insert(body.data.vertices[i].co, i)
        tree.balance()
        trees[region] = tree

    def normalize(row):
        row = sorted(((n, w) for n, w in row.items() if w > 1e-6),
                     key=lambda item: (-item[1], item[0]))[:4]
        total = sum(w for _, w in row)
        assert total > 0
        return {n: w/total for n, w in row}

    def initialize(p, region):
        row = {}
        for _, i, distance in trees[region].find_n(p, 4):
            factor = 1/max(.008, distance)**2
            for n, w in fields[i].items():
                if scopes[region](n): row[n] = row.get(n, 0)+w*factor
        return normalize(row)

    rows = []
    for vertex in obj.data.vertices:
        p = vertex.co
        # Final fitted arm brush determines anatomical ownership. The same
        # shared75 rest segments then author shoulder/elbow/cuff transitions.
        choices = []
        for side, anchors in targets.items():
            s, e, w = anchors
            along = (p-s).dot((e-s).normalized())
            radial = min((p-a-(b-a)*max(0., min(1., (p-a).dot(b-a)/(b-a).length_squared))).length
                         for a, b in ((s, e), (e, w)))
            alpha = smooth(.015, .10, along)*(1-smooth(.12, .19, radial))
            choices.append((alpha, side))
        alpha, side = max(choices)
        torso = initialize(p, 'torso')
        if p.z > targets[side][0].z+.06:
            rows.append(normalize({'DEF-spine.003': .65, 'DEF-spine.004': .35}))
            continue
        s, e, w = targets[side]
        candidates = []
        chain = [('DEF-upper_arm.'+side, s, (s+e)/2),
                 ('DEF-upper_arm.'+side+'.001', (s+e)/2, e),
                 ('DEF-forearm.'+side, e, (e+w)/2),
                 ('DEF-forearm.'+side+'.001', (e+w)/2, w)]
        for name, a, b in chain:
            d = b-a
            t = max(0., min(1., (p-a).dot(d)/d.length_squared))
            distance = (p-a-d*t).length
            candidates.append((name, 1/max(.02, distance)**3))
        authored = normalize(dict(candidates))
        initial = initialize(p, side)
        arm = normalize({n: .75*authored.get(n, 0)+.25*initial.get(n, 0)
                         for n in set(authored)|set(initial)})
        rows.append(normalize({n: (1-alpha)*torso.get(n, 0)+alpha*arm.get(n, 0)
                               for n in set(torso)|set(arm)}))
    obj.vertex_groups.clear()
    for name in sorted({n for row in rows for n in row}):
        obj.vertex_groups.new(name=name)
    for i, row in enumerate(rows):
        for name, weight in row.items(): obj.vertex_groups[name].add([i], weight, 'REPLACE')
    obj.modifiers.clear()
    modifier = obj.modifiers.new('Shared75SelectedHoodieSkin', 'ARMATURE')
    modifier.object = rig
    modifier.use_deform_preserve_volume = False
    obj.parent = rig
    obj.matrix_parent_inverse = Matrix.Identity(4)
    obj.matrix_world = Matrix.Identity(4)
    return rows


def author(spec, out):
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/spec['nativeMaster']['path']))
    body, rig = bpy.data.objects['RiderBody'], bpy.data.objects['RiderSkeleton']
    assert len(body.data.vertices) == 10582 and len(rig.data.bones) == 75
    before = signature(body, rig)
    targets = target_arms(rig)
    spec['targetHemZ'] = rig.data.bones['DEF-spine'].head_local.z+spec['hemAbovePelvisM']
    historical = []
    for old in list(bpy.data.objects):
        if old.type == 'MESH' and (old.name == 'RiderHoodie' or old.name.startswith('RiderHoodie.')):
            assert old != body
            old.name = 'HistoricalReference_'+old.name
            old.hide_render = True
            old.hide_viewport = True
            if old.name in bpy.context.scene.objects: old.hide_set(True)
            historical.append(old.name)
    with bpy.data.libraries.load(str(ROOT/spec['selectedNative']['path']), link=False) as (available, selected):
        assert spec['sourceObject'] in available.objects
        selected.objects = [spec['sourceObject']]
    obj = selected.objects[0]
    bpy.context.scene.collection.objects.link(obj)
    assert len(obj.data.vertices) == 12430 and len(obj.data.polygons) == 19878
    basis = Matrix(((0., 1., 0.), (-1., 0., 0.), (0., 0., 1.)))
    original = [basis @ (obj.matrix_world @ v.co) for v in obj.data.vertices]
    obj.parent = None
    obj.matrix_world = Matrix.Identity(4)
    obj.modifiers.clear()
    obj.vertex_groups.clear()
    obj.name = 'RiderHoodie'
    assert obj.name == 'RiderHoodie' and bpy.data.objects['RiderHoodie'] == obj, \
        'Actual selected hoodie did not acquire its exact production name'
    obj.hide_render = False
    obj.hide_viewport = False
    obj.hide_set(False)
    # Direct proportional edits preserve original hood/hem/cuffs/major folds.
    for v, p in zip(obj.data.vertices, original): v.co = fit_point(p, spec, targets)[0]
    obj.data.update()
    obj['unaccepted'] = True
    obj['selectedNativeSHA256'] = spec['selectedNative']['sha256']
    obj['originalDenseSHA256'] = spec['originalDensePaint']['sha256']
    obj['productionHoodieRecipeSHA256'] = sha(__file__)
    obj['changedTopologyNeedsDenseBake'] = True
    # Preserve the real fitted selected surface before a destructive local
    # topology edit, so even a failed grid fill leaves an editable fit.
    fit_native = out/'proportional-fit-before-patch.blend'
    assert signature(body, rig) == before
    assert not body.hide_render and not body.hide_viewport and not body.hide_get()
    bpy.ops.wm.save_as_mainfile(filepath=str(fit_native), compress=True)
    fitted = {'accepted': False, 'stage': 'SELECTED_FIT_SAVED_BEFORE_AXILLA_TOPOLOGY',
              'native': {'path': str(fit_native), 'sha256': sha(fit_native)},
              'targetObject': obj.name, 'targetGeometrySHA256': hoodie_geometry(obj),
              'recipeSHA256': sha(__file__), 'sourceNativeSHA256': spec['selectedNative']['sha256'],
              'bodyAnd75RigUnchanged': True,
              'limits': ['Unrigged proportional fit only; topology, bake and motion remain pending.']}
    (out/'proportional-fit.json').write_text(json.dumps(fitted, indent=2)+'\n')
    try:
        topology = rebuild_axilla(obj, spec, targets)
    except Exception as error:
        (out/'patch-failure.json').write_text(json.dumps({
            'accepted': False, 'stage': 'AXILLA_TOPOLOGY_FAILED_FITTED_NATIVE_PRESERVED',
            'recipeSHA256': sha(__file__), 'fittedNative': fitted['native'],
            'failure': {'type': type(error).__name__, 'message': str(error)}}, indent=2)+'\n')
        raise
    rows = skin(obj, body, rig, spec, targets)
    # Editable landmark controls document the direct edit in the saved scene.
    for side, anchors in targets.items():
        for label, p in zip(('Shoulder', 'Elbow', 'Cuff'), anchors):
            marker = bpy.data.objects.new('HoodieFit'+label+'.'+side, None)
            bpy.context.collection.objects.link(marker)
            marker.location = p
            marker.empty_display_type = 'SPHERE'
            marker.empty_display_size = .018
            marker.hide_render = True
    assert signature(body, rig) == before
    assert not body.hide_render and not body.hide_viewport and not body.hide_get()
    assert all(bpy.data.objects[name].hide_render and bpy.data.objects[name].hide_viewport
               for name in historical), 'Historical coarse hoodie can display'
    assert not any(o != obj and o.type == 'MESH' and o.name.startswith('RiderHoodie')
                   for o in bpy.context.scene.objects), 'Duplicate named hoodie in saved scene'
    native = out/'authored-hoodie.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(native), compress=True)
    np.savez_compressed(out/'hoodie-fields.npz', vertices=np.array([list(v.co) for v in obj.data.vertices]),
                        fields=np.array([[row.get(b.name, 0) for b in rig.data.bones] for row in rows]),
                        jointNames=np.array([b.name for b in rig.data.bones]))
    receipt = {'accepted': False, 'stage': 'AUTHORED_MESH_SAVED_BEFORE_MAPS',
               'recipeSHA256': sha(__file__), 'inputs': spec, 'bodyAnd75RigSignature': before,
               'bodyAnd75RigUnchanged': True, 'completeBodyVisible': True,
               'native': {'path': str(native), 'sha256': sha(native)},
               'fittedBeforeTopology': fitted['native'],
               'vertices': len(obj.data.vertices), 'polygons': len(obj.data.polygons),
               'targetObject': obj.name, 'targetGeometrySHA256': hoodie_geometry(obj),
               'hiddenHistoricalGarments': historical,
               'underarmPatches': topology,
               'limits': ['Changed axilla UV/material awaits actual dense bake.',
                          'No rest-fit or moving-art acceptance; parent judges full outfit.']}
    (out/'author.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print('SELECTED_HOODIE_AUTHORED', json.dumps(receipt['underarmPatches']), flush=True)


def bake(spec, out, author_out):
    receipt = json.loads((author_out/'author.json').read_text())
    assert receipt['inputs'] == spec or {k: v for k, v in receipt['inputs'].items() if k != 'targetHemZ'} == spec
    native = Path(receipt['native']['path'])
    assert sha(native) == receipt['native']['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(native))
    body, rig, obj = (bpy.data.objects[n] for n in ('RiderBody', 'RiderSkeleton', 'RiderHoodie'))
    assert obj.name == receipt['targetObject'] == 'RiderHoodie'
    assert hoodie_geometry(obj) == receipt['targetGeometrySHA256'], 'Bake selected a different mesh'
    assert obj['selectedNativeSHA256'] == spec['selectedNative']['sha256']
    assert obj['originalDenseSHA256'] == spec['originalDensePaint']['sha256']
    assert obj['productionHoodieRecipeSHA256'] == receipt['recipeSHA256'] == sha(__file__)
    assert all(bpy.data.objects[name].hide_render and bpy.data.objects[name].hide_viewport
               for name in receipt['hiddenHistoricalGarments'])
    before = signature(body, rig)
    targets = target_arms(rig)
    spec['targetHemZ'] = receipt['inputs']['targetHemZ']
    prior = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(ROOT/spec['originalDensePaint']['path']))
    dense = [o for o in bpy.data.objects if o not in prior and o.type == 'MESH']
    assert dense and sum(len(o.data.polygons) for o in dense) > 500000
    for o in dense:
        original = [o.matrix_world @ v.co for v in o.data.vertices]
        o.parent = None
        o.matrix_world = Matrix.Identity(4)
        for v, p in zip(o.data.vertices, original): v.co = fit_point(p, spec, targets, dense=True)[0]
        o.data.update()
        o.hide_render = False
        o.hide_set(False)
    # A fresh conventional atlas carries all four real selected dense channels.
    active(obj)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=.008)
    bpy.ops.object.mode_set(mode='OBJECT')
    obj.data.uv_layers.active.name = 'SelectedDenseHoodieProductionAtlas'
    target_material = bpy.data.materials.new('SelectedDenseHoodieProductionPBR')
    target_material.use_nodes = True
    obj.data.materials.clear()
    obj.data.materials.append(target_material)
    for face in obj.data.polygons: face.material_index = 0
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = spec['bake']['samples']
    scene.render.bake.use_selected_to_active = True
    scene.render.bake.cage_extrusion = spec['bake']['cageExtrusionM']
    scene.render.bake.max_ray_distance = spec['bake']['maxRayDistanceM']
    scene.render.bake.margin = spec['bake']['marginPx']
    modifier = next(m for m in obj.modifiers if m.type == 'ARMATURE')
    modifier.show_viewport = False
    modifier.show_render = False
    originals = {o.name: list(o.data.materials) for o in dense}
    images = {}
    channels = [('baseColor', 'Base Color'), ('roughness', 'Roughness'), ('metallic', 'Metallic'), ('normal', None)]
    for channel, socket in channels:
        for o in dense:
            o.data.materials.clear()
            for original in originals[o.name]:
                if socket is None:
                    o.data.materials.append(original)
                    continue
                material = original.copy()
                principled = next(n for n in material.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
                output = next(n for n in material.node_tree.nodes if n.type == 'OUTPUT_MATERIAL')
                emission = material.node_tree.nodes.new('ShaderNodeEmission')
                value = principled.inputs[socket]
                if value.is_linked:
                    material.node_tree.links.new(value.links[0].from_socket, emission.inputs['Color'])
                elif socket == 'Base Color':
                    emission.inputs['Color'].default_value = value.default_value
                else:
                    emission.inputs['Color'].default_value = (value.default_value,)*3+(1,)
                material.node_tree.links.new(emission.outputs[0], output.inputs['Surface'])
                o.data.materials.append(material)
        size = spec['bake']['size']
        image = bpy.data.images.new('ActualSelectedDenseHoodie-'+channel, width=size, height=size, alpha=False)
        image.colorspace_settings.name = 'sRGB' if channel == 'baseColor' else 'Non-Color'
        node = target_material.node_tree.nodes.new('ShaderNodeTexImage')
        node.image = image
        target_material.node_tree.nodes.active = node
        active(obj)
        for o in dense: o.select_set(True)
        print('SELECTED_HOODIE_BAKE', channel, flush=True)
        bpy.ops.object.bake(type='NORMAL' if channel == 'normal' else 'EMIT')
        image.filepath_raw = str(out/(channel+'.png'))
        image.file_format = 'PNG'
        image.save()
        image.pack()
        images[channel] = (image, node)
    nodes, links = target_material.node_tree.nodes, target_material.node_tree.links
    principled = nodes.get('Principled BSDF')
    for channel, socket in channels[:3]: links.new(images[channel][1].outputs['Color'], principled.inputs[socket])
    normal = nodes.new('ShaderNodeNormalMap')
    links.new(images['normal'][1].outputs['Color'], normal.inputs['Color'])
    links.new(normal.outputs['Normal'], principled.inputs['Normal'])
    modifier.show_viewport = True
    modifier.show_render = True
    for o in dense:
        o.hide_render = True
        o.hide_set(True)
        o['actualSelectedBakeSource'] = spec['originalDensePaint']['sha256']
    obj['changedTopologyNeedsDenseBake'] = False
    assert signature(body, rig) == before == receipt['bodyAnd75RigSignature']
    assert not body.hide_render and not body.hide_viewport and not body.hide_get()
    native = out/'selected-hoodie.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(native), compress=True)
    result = {'accepted': False, 'stage': 'ACTUAL_SELECTED_DENSE_PBR_BAKED_UNREVIEWED',
              'recipeSHA256': sha(__file__), 'authorReceiptSHA256': sha(author_out/'author.json'),
              'originalDenseSHA256': spec['originalDensePaint']['sha256'],
              'native': {'path': str(native), 'sha256': sha(native)},
              'maps': {n: {'path': str(out/(n+'.png')), 'sha256': sha(out/(n+'.png'))} for n in images},
              'bodyAnd75RigUnchanged': True, 'completeBodyVisible': True,
              'limits': ['Actual bake rays/misses/seams and selected appearance need parent comparison.',
                         'Full-outfit played native and Garage/game review pending. No player promotion.']}
    (out/'bake.json').write_text(json.dumps(result, indent=2)+'\n')


def main():
    args = sys.argv[sys.argv.index('--')+1:]
    assert len(args) in (3, 4)
    specpath, out, stage = Path(args[0]).resolve(), Path(args[1]).resolve(), args[2]
    assert out.is_relative_to(ROOT/'harness/out/rider-rebuild/production-hoodie01')
    assert not out.exists(), 'Fresh output leaf required'
    spec = json.loads(specpath.read_text())
    for key in SOURCE_KEYS:
        assert sha(ROOT/spec[key]['path']) == spec[key]['sha256'], ('Input changed', key)
    out.mkdir(parents=True)
    if stage == 'author':
        assert len(args) == 3
        author(spec, out)
    elif stage == 'bake':
        assert len(args) == 4
        bake(spec, out, Path(args[3]).resolve())
    else: raise AssertionError('Stage must be author or bake')
    for key in SOURCE_KEYS:
        assert sha(ROOT/spec[key]['path']) == spec[key]['sha256'], ('Input changed', key)


if __name__ == '__main__':
    main()
