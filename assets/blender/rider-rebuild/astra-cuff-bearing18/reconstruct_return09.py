"""Reconstruct the cavity-rooted inward cuff return, retaining its exterior.

The authored rim follows the source surface's radial tangency. Only the inward
component reached from the measured inner cut loop is removed: disconnected
exterior undercuts remain. This is an unaccepted topology/material construction.
"""
from collections import defaultdict, deque

import numpy as np


def edges_of(surgery, ids):
    edges = defaultdict(list)
    for i in ids:
        face = surgery.faces[i]
        for k, (a, b) in enumerate(zip(face, face[1:]+face[:1])):
            edges[tuple(sorted((a, b)))].append((i, k, a, b))
    assert all(len(rows) <= 2 for rows in edges.values()), 'Nonmanifold source cuff'
    return edges


def ring_components(edges):
    graph = defaultdict(list)
    for _, _, a, b in edges:
        graph[a].append(b); graph[b].append(a)
    assert graph and all(len(row) == 2 for row in graph.values()), 'Rim is not a simple ring'
    unseen = set(graph); result = []
    while unseen:
        reached = {min(unseen)}; todo = list(reached)
        while todo:
            for n in graph[todo.pop()]:
                if n not in reached:
                    reached.add(n); todo.append(n)
        unseen.difference_update(reached); result.append(sorted(reached))
    return result


def one_ring(edges):
    rings = ring_components(edges)
    assert len(rings) == 1, 'Measured floor boundary is not one ring'
    return rings[0]


def remove_inner_return(surgery, inner_cut, x, z, settings):
    source = np.asarray(surgery.source, dtype=float)
    faces = np.asarray(surgery.faces, dtype=int)
    selected = np.flatnonzero(np.all(source[faces, 1] <= settings['gloveFloorCutY']+1e-8, axis=1))
    edge_map = edges_of(surgery, selected)
    inner_keys = {tuple(sorted((a, b))) for _, _, a, b in inner_cut}
    outer_cut = [rows[0] for key, rows in edge_map.items()
                 if len(rows) == 1 and key not in inner_keys]
    inner_ids = one_ring(inner_cut); outer_ids = one_ring(outer_cut)
    assert all(abs(source[v, 1]-settings['gloveFloorCutY']) < 1e-8 for v in outer_ids)
    # Establish that later detached pieces were created by return removal,
    # rather than silently deleting an inherited separate selected ornament.
    original_graph = defaultdict(list)
    for rows in edge_map.values():
        if len(rows) == 2:
            p, q = rows[0][0], rows[1][0]
            original_graph[p].append(q); original_graph[q].append(p)
    connected = {outer_cut[0][0]}; todo = list(connected)
    while todo:
        for n in original_graph[todo.pop()]:
            if n not in connected:
                connected.add(n); todo.append(n)
    assert connected == set(selected), 'Source cuff has a separate inherited component'
    normals = np.zeros_like(source)
    face_normals = np.cross(source[faces[:, 1]]-source[faces[:, 0]],
                            source[faces[:, 2]]-source[faces[:, 0]])
    for corner in range(3):
        np.add.at(normals, faces[:, corner], face_normals)
    normals /= np.maximum(np.linalg.norm(normals, axis=1)[:, None], 1e-30)
    radial = np.column_stack((x, np.zeros(len(source)), z))
    radial /= np.maximum(np.linalg.norm(radial, axis=1)[:, None], 1e-30)
    signed = -np.sum(normals*radial, axis=1)
    if np.mean(signed[inner_ids]) < 0:
        signed *= -1
    assert np.min(signed[inner_ids]) > 0 and np.max(signed[outer_ids]) < 0, 'Source cut does not distinguish cavity and exterior'
    inward = np.zeros(len(faces), dtype=bool)
    inward[selected] = np.max(signed[faces[selected]], axis=1) > 1e-10
    graph = defaultdict(list)
    for (a, b), rows in edge_map.items():
        if len(rows) == 2 and max(signed[a], signed[b]) > 1e-10:
            p, q = rows[0][0], rows[1][0]
            if inward[p] and inward[q]:
                graph[p].append(q); graph[q].append(p)
    seeds = {row[0] for key in inner_keys for row in edge_map[key]}
    reached = {min(seeds)}; todo = deque(reached)
    while todo:
        for other in graph[todo.popleft()]:
            if other not in reached:
                reached.add(other); todo.append(other)
    assert seeds <= reached, 'Cavity cut reaches disconnected inward sheets'
    outer_witness = [106802, 106804, 107801]
    inner_witness = [106803, 106805, 105797]
    assert np.max(signed[outer_witness]) < 0 and np.min(signed[inner_witness]) > 0
    witness_face = np.flatnonzero(np.all(np.sort(faces, axis=1) == sorted(inner_witness), axis=1))
    assert len(witness_face) == 1 and int(witness_face[0]) in reached
    candidates = np.zeros(len(faces), dtype=bool); candidates[list(reached)] = True
    crossing = candidates & (np.min(signed[faces], axis=1) < -1e-10)
    assert np.all(faces[crossing] < surgery.old_count), 'Authored rim unexpectedly intersects a previous cut'
    removed = np.flatnonzero(candidates & (np.min(signed[faces], axis=1) > 1e-10))
    clipped = np.flatnonzero(crossing)
    removed_source_ids = sorted({int(surgery.face_sources[i]) for i in removed})
    clipped_source_ids = sorted({int(surgery.face_sources[i]) for i in clipped})
    surgery.cut(signed, candidates)
    # Keep the entire sheet connected to the measured OUTER source cut,
    # including its external undercuts. A secondary real boundary circuit
    # belongs to this selected sheet; it must be sewn, not guessed away.
    current_source = np.asarray(surgery.source)
    current_faces = np.asarray(surgery.faces)
    current_band = np.flatnonzero(np.all(current_source[current_faces, 1] <= settings['gloveFloorCutY']+1e-8, axis=1))
    current_edges = edges_of(surgery, current_band)
    attached_graph = defaultdict(list)
    for rows in current_edges.values():
        if len(rows) == 2:
            p, q = rows[0][0], rows[1][0]
            attached_graph[p].append(q); attached_graph[q].append(p)
    outer_keys = {tuple(sorted(edge[2:])) for edge in outer_cut}
    attached_seeds = {row[0] for key in outer_keys for row in current_edges[key]}
    attached = {min(attached_seeds)}; todo = list(attached)
    while todo:
        for n in attached_graph[todo.pop()]:
            if n not in attached:
                attached.add(n); todo.append(n)
    assert attached_seeds <= attached, 'The measured outer cut was disconnected'
    detached = sorted(set(current_band)-attached)
    assert not detached, 'Return removal detached a source patch; do not delete it to force a rim'
    remaining = np.asarray(surgery.faces)
    assert np.any(np.all(np.sort(remaining, axis=1) == sorted(outer_witness), axis=1)), 'Selected exterior witness was lost'
    rim = [rows[0] for rows in edges_of(surgery, range(len(surgery.faces))).values() if len(rows) == 1]
    rim_rings = ring_components(rim)
    rim_ids = [v for ring in rim_rings for v in ring]
    assert np.max(np.asarray(surgery.source)[rim_ids, 1]) < settings['gloveFloorCutY']-1e-6
    return rim, {
        'method': 'Area-weighted actual source normal dot source radial direction; remove only the inward connected component rooted at the measured inner cut. The zero contour is an authored tangent rim, not a claimed original seam.',
        'removedSourceFaceIds': removed_source_ids, 'rimClippedSourceFaceIds': clipped_source_ids,
        'originalCuffConnectedBeforeRemoval': True,
        'retainedCuffConnectedToMeasuredOuterCut': True,
        'removedCompleteTriangles': len(removed), 'clippedRimTriangles': len(clipped),
        'authoredRimVertices': len(rim_ids),
        'actualAuthoredBoundaryCircuitVertices': [len(ring) for ring in rim_rings],
        'allActualBoundaryCircuitsSewnWithoutCaps': True,
        'sourceRimYRange': [float(np.asarray(surgery.source)[rim_ids, 1].min()), float(np.asarray(surgery.source)[rim_ids, 1].max())],
        'retainedExteriorWitness': outer_witness, 'removedInnerWitness': inner_witness,
        'innerWitnessInwardValues': signed[inner_witness].tolist(),
        'outerWitnessInwardValues': signed[outer_witness].tolist(),
        'detailChange': 'Original cavity-facing return and its inward half of the rounded lip are replaced; selected outward surface, external undercuts and source UV/material ancestry remain. Moving art review must judge the rebuilt lip.',
    }


def fit_exterior(surgery, face_ids, profile, wearer, settings, B):
    source = np.asarray(surgery.source); base = np.asarray(surgery.world)
    all_faces = np.asarray(surgery.faces, dtype=int); faces = all_faces[face_ids]
    support_faces = all_faces[np.any(source[all_faces, 1] < settings['gloveJoinY'], axis=1)]
    native = np.unique(support_faces)
    inverse = np.full(len(source), -1, dtype=int); inverse[native] = np.arange(len(native))
    f = inverse[support_faces]
    edges = np.unique(np.sort(np.concatenate((f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]])), axis=1), axis=0)
    a, b = edges[:, 0], edges[:, 1]
    degree = np.bincount(np.r_[a, b], minlength=len(native)).astype(float)
    p = base[native]; s = np.sum((p-profile.wrist)*profile.axis, axis=1)
    radial = p-profile.wrist-s[:, None]*profile.axis
    radii = np.linalg.norm(radial, axis=1); assert np.all(radii > 1e-8)
    directions = radial/radii[:, None]
    fixed = source[native, 1] >= settings['gloveJoinY']
    displacement = np.zeros(len(native)); lower = np.zeros(len(native))
    cloth_budget = settings['sleeveSkinEaseM']+settings['sleeveLiningM']+settings['garmentGapM']
    outer_budget = cloth_budget+settings['cuffLiningM']
    barycentrics = np.array([[1/3, 1/3, 1/3], [.9, .05, .05], [.05, .9, .05], [.05, .05, .9]])
    history = []; world = base.copy(); final_probes = 0
    for contact_pass in range(settings['cuffContactPasses']+1):
        deficits = 0; maximum = 0.; probes = 0
        for face in faces:
            tri = world[face]
            if np.linalg.norm(np.cross(tri[1]-tri[0], tri[2]-tri[0])) < 1e-14:
                continue  # Inherited/new degenerates remain mandatory geometry failures.
            local = inverse[face]
            for bary in barycentrics:
                point = np.sum(tri*bary[:, None], axis=0)
                station = float((point-profile.wrist)@profile.axis)
                origin = profile.wrist+station*profile.axis
                vector = point-origin; radius = float(np.linalg.norm(vector)); assert radius > 1e-8
                direction = vector/radius
                body = B.hit_radius(wearer, origin, direction)
                assert body is not None, ('Actual wearer missing at retained cuff exterior', face.tolist(), bary.tolist())
                need = body+outer_budget-radius; probes += 1; maximum = max(maximum, need)
                if need > settings['contactConvergenceM']:
                    cosines = directions[local]@direction
                    assert np.min(cosines) > 0, 'A retained exterior triangle wraps the anatomical axis'
                    np.maximum.at(lower, local, displacement[local]+need/float(cosines.min()))
                    deficits += 1
        history.append({'pass': contact_pass, 'actualTriangleInteriorBearings': probes,
                        'violatingBearings': deficits, 'maximumClearanceDeficitM': maximum})
        assert probes > 1000
        if deficits == 0:
            final_probes = probes; break
        assert contact_pass < settings['cuffContactPasses'], ('Cuff exterior contact did not settle', history)
        assert np.all(lower[fixed] == 0), 'Contact escaped the owned source cuff/join'
        delta = float('inf')
        for iteration in range(settings['contactIterations']):
            sums = np.bincount(np.r_[a, b], weights=np.r_[displacement[b], displacement[a]], minlength=len(native))
            target = np.maximum(sums/(degree+settings['contactPositionPenalty']), lower)
            target[fixed] = 0
            following = .5*displacement+.5*target
            delta = float(np.max(abs(following-displacement))); displacement = following
            if delta < settings['contactConvergenceM']:
                break
        assert delta < settings['contactConvergenceM'], ('Cuff contact field did not converge', delta)
        assert float(np.max((radii+displacement)/radii)) <= settings['maximumCuffScale'], 'Local exterior correction exceeds the unchanged identity guard'
        world[native] = base[native]+displacement[:, None]*directions
    changed = native[displacement > 0]
    surgery.move(world, changed)
    return {
        'sourceTransverseUniformScale': 1., 'actualTriangleInteriorBearings': final_probes,
        'contactPasses': history, 'changedRetainedExteriorAndJoinVertices': len(changed),
        'maximumLocalDisplacementM': float(displacement.max()),
        'maximumLocalRadiusRatio': float(np.max((radii+displacement)/radii)),
        'sourceBeyondJoinFixed': True, 'cuffLiningM': settings['cuffLiningM'],
        'explicitSleeveLayersM': {'skinEase': settings['sleeveSkinEaseM'], 'sleeveWall': settings['sleeveLiningM'], 'clothGloveGap': settings['garmentGapM']},
        'requiredCavityReserveM': cloth_budget, 'requiredExteriorReserveM': outer_budget,
        'oldFixedCavityReserveM': settings['gloveCavityEaseM'],
        'method': 'Minimal graph contact displacement of the retained selected exterior; no uniform cuff enlargement and no old inner-return radial constraint. Four interior bearings per retained nondegenerate source triangle are checked against actual wearer triangles. The current explicit sleeve layers reserve the real cavity; subsequent sleeve contact and dense checks remain required.',
    }


def reconstruct(surgery, dump, placement, profile, wearer, settings, B):
    inner_cut, floor = B.floor_cut(surgery, dump, settings['gloveFloorCutY'])
    scale, x_basis, z_basis = B.V['cuff_frame'](dump, placement)
    source = np.asarray(surgery.source)
    axial, x, z = B.V['source_cuff'](source, dump, settings['sourceWrist'], scale, x_basis, z_basis)
    rim, ownership = remove_inner_return(surgery, inner_cut, x, z, settings)
    source = np.asarray(surgery.source); before = np.asarray(surgery.world)
    axial, x, z = B.V['source_cuff'](source, dump, settings['sourceWrist'], scale, x_basis, z_basis)
    proposed = profile.wrist+axial[:, None]*profile.axis+x[:, None]*x_basis+z[:, None]*z_basis
    alpha = B.smooth((settings['gloveJoinY']-source[:, 1])/(settings['gloveJoinY']-settings['gloveFullY']))
    surgery.move(before+alpha[:, None]*(proposed-before), np.flatnonzero(alpha > 0))
    faces = np.asarray(surgery.faces)
    exterior = np.flatnonzero(np.all(source[faces, 1] <= settings['gloveFloorCutY']+1e-8, axis=1))
    fitting = fit_exterior(surgery, exterior, profile, wearer, settings, B)
    outer_edges = [rows[0] for rows in edges_of(surgery, exterior).values() if len(rows) == 1]
    proximal = [edge for edge in outer_edges if abs(source[edge[2], 1]-settings['gloveFloorCutY']) < 1e-8 and abs(source[edge[3], 1]-settings['gloveFloorCutY']) < 1e-8]
    one_ring(proximal); ring_components(rim)
    assert len(outer_edges) == len(proximal)+len(rim)
    world = np.asarray(surgery.world); duplicate = {}
    for vertex in np.unique(np.asarray(surgery.faces)[exterior]):
        p = world[vertex]; axial = float((p-profile.wrist)@profile.axis)
        radial = p-profile.wrist-axial*profile.axis
        radius = float(np.linalg.norm(radial)); assert radius > settings['cuffLiningM']
        inside = p-settings['cuffLiningM']*radial/radius
        duplicate[int(vertex)] = surgery.add(surgery.source[vertex], inside, surgery.parents[vertex], surgery.coefficients[vertex], 3)
    lining = []
    for i in exterior:
        lining.append(len(surgery.faces))
        surgery.add_face([duplicate[v] for v in surgery.faces[i][::-1]], surgery.uv[i][::-1], surgery.material[i])
    # Corresponding source boundary edges sew the true nonplanar authored rim.
    # No radial sorting, planar cap, centroid ring or guessed aperture is used.
    for i, corner, a, b in rim:
        uva, uvb = surgery.uv[i][corner], surgery.uv[i][(corner+1) % 3]
        third = surgery.uv[i][(corner+2) % 3]
        ia, ib = duplicate[a], duplicate[b]
        va, vb = .96*uva+.04*third, .96*uvb+.04*third
        surgery.add_face([b, a, ia], [uvb, uva, va], surgery.material[i])
        surgery.add_face([b, ia, ib], [uvb, va, vb], surgery.material[i])
    line_edges = [rows[0] for rows in edges_of(surgery, lining).values() if len(rows) == 1]
    proximal_set = {duplicate[v] for edge in proximal for v in edge[2:]}
    open_inner = [edge for edge in line_edges if edge[2] in proximal_set and edge[3] in proximal_set]
    one_ring(open_inner)
    extension = B.lining(surgery, open_inner, profile.axis, profile.wrist, settings['cuffLiningM'], -settings['gloveLiningLengthM'], profile=profile)
    floor.update(returnOwnership=ownership, exteriorContact=fitting,
                 newCuffLiningVertices=len(duplicate), newCuffLiningTriangles=len(lining),
                 newNonplanarRimTriangles=2*len(rim), wristLiningExtension=extension,
                 sourceTransverseUniformScale=1.,
                 newLiningAncestry='Each reversed thin-lining face copies its retained exterior source-parent interpolation, corner UV and material. The paired rim edges retain exact source order; authored UV strips lie within the adjacent source triangle.',
                 limits='Source-only local reconstruction until actual construction, all dense geometry checks, and moving selected-material review pass. Inward return/lip detail changes are explicit; no accepted-art claim.')
    return floor
